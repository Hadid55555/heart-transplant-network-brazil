# Bloco 3 — Volume do centro × óbito hospitalar: termos entre e dentro do centro, categorias, GEE e conferência
# Uso: LANG=C.UTF-8 Rscript scripts/bloco3_volume.R data_2000_w04 outputs_2000_2025/bloco3
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; out <- if (length(args) >= 2) args[2] else "outputs/bloco3"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
suppressPackageStartupMessages({ library(geepack); library(glmmTMB) })
dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco3.txt"), split = TRUE)
cat("Bloco 3 —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d

# ---------------------------------------------------------------- descrição dos clusters
tam <- d[, .(n = .N, obitos = sum(morte)), by = centro]
cat(sprintf("\nCentros: %d | AIH por centro: mín %d, P25 %.1f, mediana %.0f, P75 %.1f, máx %d | centros sem óbito: %d\n",
            nrow(tam), min(tam$n), quantile(tam$n, .25), median(tam$n), quantile(tam$n, .75), max(tam$n), sum(tam$obitos == 0)))
dist_tam <- tam[, .(centros = .N, AIH = sum(n), obitos = sum(obitos)),
                by = .(faixa = cut(n, c(0, 4, 9, 19, 49, 99, Inf), labels = c("1-4", "5-9", "10-19", "20-49", "50-99", ">=100")))][order(faixa)]
print(dist_tam)

# ---------------------------------------------------------------- spline do volume
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9)))
cat("\nNós de 'entre' (P10, P50, P90 nas AIH):", round(kE, 2), "\n")
cat("Nota: P90 de 'entre' coincide com o máximo (o maior centro tem", max(tam$n), "AIH =", round(100 * max(tam$n) / nrow(d), 1), "% das AIH).\n")
add_rcs(d, "entre", kE, "e")
f_main <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
f_lin  <- morte ~ e1 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
cat("\n== Modelo principal (multinível)\n")
fit <- escada(f_main, d, f_lin, "H1 principal")
m <- fit$m
if (!inherits(m, "glmerMod")) stop("Modelo principal não convergiu como multinível (passo ", fit$passo, "): rever antes de seguir")
print(summary(m)$coefficients)

vals <- c(P10 = kE[1], `5` = 5, `10` = 10, `20` = 20, `30` = 30, `40` = 40, P90 = kE[3])
Lmat <- function(v) { B <- rcs2(c(v, kE[2]), kE); x <- B[1, ] - B[2, ]; nb <- union(nomes_b(fit), c("e1", "e2")); z <- setNames(rep(0, length(nb)), nb); z[c("e1", "e2")] <- x; z }
Lm <- do.call(rbind, lapply(vals, Lmat))
nomes_c <- paste0("Entre: V−1 médio = ", c("P10 (", "", "", "", "", "", "P90 ("), c(fmt(kE[1], 1), "5", "10", "20", "30", "40", fmt(kE[3], 1)),
                  c(")", "", "", "", "", "", ")"), " vs P50 (", fmt(kE[2], 1), ")")
nb <- union(nomes_b(fit), c("e1", "e2")); Ld <- matrix(0, 1, length(nb), dimnames = list(NULL, nb)); Ld[, "dentro10"] <- 1
Lall <- rbind(Lm, Ld); nomes_all <- c(nomes_c, "Dentro: +10 TxC/ano acima da média do centro")
res_ml <- or_contraste(fit, Lall, nomes_all)
m_sem_entre <- update(m, . ~ . - e1 - e2); m_lin_entre <- update(m, . ~ . - e2)
lrt_global <- anova(m_sem_entre, m); lrt_nl <- anova(m_lin_entre, m)
cat("\nOR (multinível):\n"); print(res_ml[, .(contraste, OR = round(OR, 3), lo = round(lo, 3), hi = round(hi, 3), p = signif(p, 3))])
cat(sprintf("LRT entre (2 gl): χ² = %.2f, p = %.3g | não linearidade (1 gl): χ² = %.2f, p = %.3g\n",
            lrt_global$Chisq[2], lrt_global$`Pr(>Chisq)`[2], lrt_nl$Chisq[2], lrt_nl$`Pr(>Chisq)`[2]))
icc <- icc_mor(m); print(icc)
cov_ml <- or_tab(fit, c("faixa5<18", "faixa540-49", "faixa550-59", "faixa560+", "sexoFF"))

# ---------------------------------------------------------------- volume em categorias
cat("\n== Volume em categorias (V; ref. <10)\n")
fitc <- escada(morte ~ Vcat + faixa5 + sexoF + a1 + a2 + (1 | centro), d, NULL, "categorias")
res_cat <- or_tab(fitc, grep("^Vcat", nomes_b(fitc), value = TRUE))
print(res_cat)
cat_n <- d[, .(AIH = .N, obitos = sum(morte)), by = Vcat][order(Vcat)]

# ---------------------------------------------------------------- GEE
cat("\n== GEE exchangeable\n")
dg <- copy(d); setorder(dg, centro); dg[, id := as.integer(centro)]
f_gee <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2
g <- geeglm(f_gee, id = id, data = dg, family = binomial, corstr = "exchangeable")
bg <- coef(g); Vg <- vcov(g)
cat("Correlação exchangeable (alpha):", signif(g$geese$alpha, 3), "\n")
Lg <- Lall[, names(bg)]
est_g <- drop(Lg %*% bg); se_g <- sqrt(diag(Lg %*% Vg %*% t(Lg)))
cl <- split(seq_len(nrow(dg)), dg$id); B <- as.integer(Sys.getenv("B_BOOT", "1000"))   # 1000 na análise; valor menor só para teste rápido
RNGkind("L'Ecuyer-CMRG"); set.seed(20261013)   # bootstrap paralelo reprodutível (núcleos em NUCLEOS)
bt_l <- parallel::mclapply(seq_len(B), function(b) {
  s <- sample(names(cl), length(cl), replace = TRUE)
  db <- dg[unlist(cl[s])]; db[, id := rep(seq_along(s), lengths(cl[s]))]
  r <- tryCatch(suppressWarnings(coef(geeglm(f_gee, id = id, data = db, family = binomial, corstr = "exchangeable"))), error = function(e) NULL)
  if (is.null(r) || any(!is.finite(r)) || length(r) != length(bg)) rep(NA_real_, length(bg)) else r
}, mc.cores = as.integer(Sys.getenv("NUCLEOS", "3")), mc.set.seed = TRUE)
bt <- do.call(rbind, bt_l); falhas <- sum(!complete.cases(bt))
RNGkind("Mersenne-Twister"); set.seed(20261013)
bt <- bt[complete.cases(bt), , drop = FALSE]
cat("Bootstrap de centros:", nrow(bt), "válidas;", falhas, "falhas\n")
ct_bt <- bt %*% t(Lg)
res_gee <- data.table(contraste = nomes_all, OR = exp(est_g),
  lo_sanduiche = exp(est_g - 1.96 * se_g), hi_sanduiche = exp(est_g + 1.96 * se_g),
  lo_boot = exp(apply(ct_bt, 2, quantile, 0.025)), hi_boot = exp(apply(ct_bt, 2, quantile, 0.975)))
print(res_gee[, lapply(.SD, function(x) if (is.numeric(x)) round(x, 3) else x)])

# ---------------------------------------------------------------- modelo auxiliar e Figura 3
kV <- as.numeric(quantile(d$Vm1, c(.1, .5, .9)))
add_rcs(d, "Vm1", kV, "v")
cat("\n== Modelo auxiliar V−1 sem decomposição (nós", kV, ")\n")
fita <- escada(morte ~ v1 + v2 + faixa5 + sexoF + a1 + a2 + (1 | centro), d, morte ~ v1 + faixa5 + sexoF + a1 + a2 + (1 | centro), "auxiliar V-1")
grid <- 0:max(d$Vm1)
nd_v <- setNames(lapply(grid, function(gv) { x <- copy(d); b <- rcs2(rep(gv, nrow(x)), kV); x[, `:=`(v1 = b[, 1], v2 = b[, 2])]; x }), grid)
curva_v <- marg(fita, nd_v)[, `:=`(V_menos_1 = as.numeric(ponto), curva = "V − 1 do ano (sem decomposição)")]
gE <- seq(0, max(d$entre), by = 1)
nd_e <- setNames(lapply(gE, function(gv) { x <- copy(d); b <- rcs2(rep(gv, nrow(x)), kE); x[, `:=`(e1 = b[, 1], e2 = b[, 2], dentro10 = 0)]; x }), gE)
curva_e <- marg(fit, nd_e)[, `:=`(V_menos_1 = as.numeric(ponto), curva = "Volume médio do centro (comparação entre centros)")]
curvas <- rbind(curva_v, curva_e)
# Figura 3: desenhada por scripts/figura3_e_loco.R a partir de Curvas_Figura3

# ---------------------------------------------------------------- diagnósticos
cor_m <- round(cor(d[, .(ano, `V-1` = Vm1, entre, dentro, ano_programa, casos_acumulados = seq_centro)], method = "spearman"), 2)
cat("\n== Correlações de Spearman\n"); print(cor_m)
pS <- ggplot(d, aes(ano, Vm1, colour = tipo_centro)) + geom_jitter(width = 0.3, height = 0, alpha = 0.3, size = 0.8) +
  scale_colour_manual(values = c(entrante = PAL[2], incumbente = PAL[1]), labels = c(entrante = LAB_ENT, incumbente = LAB_INC), name = NULL) +
  labs(x = "Ano", y = "V − 1", title = "Suporte conjunto: volume anual × ano, por tipo de centro (cada ponto = 1 AIH)") + tema
ggsave(file.path(out, "FiguraS3_suporte_conjunto.png"), pS, width = 8, height = 4.5, dpi = 200, bg = "white")
aninh <- rbindlist(list(
  or_contraste(list(m = glmer(morte ~ e1 + e2 + dentro10 + (1 | centro), d, binomial, control = glmerControl(optimizer = "bobyqa"))), Lall[, c("(Intercept)", "e1", "e2", "dentro10")], nomes_all)[, modelo := "só volume"],
  or_contraste(list(m = glmer(morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + (1 | centro), d, binomial, control = glmerControl(optimizer = "bobyqa"))), Lall[, 1:9], nomes_all)[, modelo := "+ faixa e sexo"],
  res_ml[, modelo := "+ ano (principal)"]), use.names = TRUE)
loco <- rbindlist(lapply(levels(d$centro), function(cc) {
  x <- d[centro != cc]; x[, centro := droplevels(centro)]
  r <- .fit_g(f_main, x, glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))
  if (is.null(r$m)) return(NULL)
  o <- or_contraste(list(m = r$m), Lall[c(1, 7, 8), ], nomes_all[c(1, 7, 8)])
  o[, `:=`(centro_excluido = cc, avisos = length(r$msgs))]
}))
cat("\n== Leave-one-centre-out (", nlevels(d$centro), " reajustes): faixa dos OR\n", sep = "")
print(loco[, .(min = round(min(OR), 3), max = round(max(OR), 3), avisos = sum(avisos > 0)), by = contraste])

# ---------------------------------------------------------------- conferência (glmmTMB)
tm <- glmmTMB(morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro), family = binomial, data = d)
cmp <- data.table(termo = names(fixef(m)), lme4 = fixef(m), glmmTMB = fixef(tm)$cond[names(fixef(m))])
cat("\n== Conferência lme4 × glmmTMB: |diferença| máx. dos efeitos fixos =", signif(max(abs(cmp$lme4 - cmp$glmmTMB)), 3),
    "| DP centro:", signif(sqrt(VarCorr(m)$centro[1]), 4), "×", signif(sqrt(VarCorr(tm)$cond$centro[1]), 4), "\n")
dir.create(file.path(dirname(out), "_local"), showWarnings = FALSE)   # nível da AIH: fora do controle de versão
fwrite(d[, .(id_aih, centro, morte, entre, dentro, Vm1, e1, e2, a1, a2)], file.path(dirname(out), "_local", "conf_base_modelo.csv"))
fwrite(data.table(termo = names(bg), gee_R = bg), file.path(out, "conf_gee_R.csv"))

# ---------------------------------------------------------------- Tabela 4
t4 <- merge(res_ml[, .(contraste, ML = ic(OR, lo, hi), ML_p = pfmt(p))],
            res_gee[, .(contraste, GEE = ic(OR, lo_boot, hi_boot), GEE_sand = ic(OR, lo_sanduiche, hi_sanduiche))], by = "contraste", sort = FALSE)
t4c <- merge(res_cat[, .(contraste = paste0("Categoria V ", sub("Vcat", "", termo), " vs <10"), ML = ic(OR, lo, hi), ML_p = pfmt(p))],
             cat_n[, .(contraste = paste0("Categoria V ", Vcat, " vs <10"), AIH_obitos = paste0(AIH, " / ", obitos))], by = "contraste", all = TRUE)
Tabela4 <- rbindlist(list(
  t4[, .(Parâmetro = contraste, `Multinível OR (IC95%)` = ML, p = ML_p, `GEE OR (IC95% bootstrap de centros)` = GEE, `GEE (IC95% sanduíche)` = GEE_sand)],
  data.table(Parâmetro = c(sprintf("LRT global de 'entre' (2 gl): p = %s", pfmt(lrt_global$`Pr(>Chisq)`[2])),
                           sprintf("LRT de não linearidade (1 gl): p = %s", pfmt(lrt_nl$`Pr(>Chisq)`[2])))),
  t4c[, .(Parâmetro = paste0(contraste, " (AIH/óbitos na categoria: ", AIH_obitos, ")"), `Multinível OR (IC95%)` = ML, p = ML_p)],
  icc[, .(Parâmetro = medida, `Multinível OR (IC95%)` = ic(est, lo, hi, 3))],
  data.table(Parâmetro = c(sprintf("Centros: %d (AIH por centro: mediana %.0f, IQR %.1f–%.1f, faixa %d–%d); AIH %s; óbitos %d",
                                   nrow(tam), median(tam$n), quantile(tam$n, .25), quantile(tam$n, .75), min(tam$n), max(tam$n), fmt(nrow(d), 0), sum(d$morte)),
                           sprintf("Passo da escada: principal = %d; categorias = %d; auxiliar = %d. Correlação exchangeable do GEE = %.3f; bootstrap: %d reamostragens válidas",
                                   fit$passo, fitc$passo, fita$passo, g$geese$alpha, nrow(bt))))), fill = TRUE)
fwrite(Tabela4, file.path(out, "Tabela4.csv"), bom = TRUE)
salva_xlsx(list(Tabela4 = Tabela4, ML_contrastes = res_ml, ML_covariaveis = cov_ml, ICC_MOR = icc, GEE = res_gee, Categorias = res_cat,
                Categorias_n = cat_n, Curvas_Figura3 = curvas, Correlacoes = as.data.table(cor_m, keep.rownames = "var"),
                Aninhados = aninh, LOCO = loco, Distrib_centros = dist_tam, Conferencia_glmmTMB = cmp,
                Escada = data.table(modelo = c(fit$rotulo, fitc$rotulo, fita$rotulo), passo = c(fit$passo, fitc$passo, fita$passo),
                                    log = c(paste(fit$log, collapse = " || "), paste(fitc$log, collapse = " || "), paste(fita$log, collapse = " || ")))),
           file.path(out, "Bloco3_tabelas.xlsx"))
saveRDS(list(kE = kE, kV = kV, Lall = Lall, nomes_all = nomes_all, res_ml = res_ml), file.path(out, "bloco3_objetos.rds"))
cat("\nArquivos:", paste(list.files(out), collapse = ", "), "\n")
sink()
