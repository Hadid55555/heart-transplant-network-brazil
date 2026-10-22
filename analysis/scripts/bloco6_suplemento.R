# Bloco 6 — Suplemento: captura SIH × RBT, funil, sensibilidades do modelo de volume, pandemia, tendência e reembolso
# Uso: LANG=C.UTF-8 Rscript scripts/bloco6_suplemento.R data_2000_w04 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; outs <- if (length(args) >= 2) args[2] else "outputs"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
suppressPackageStartupMessages({ library(logistf); library(survival) })
out <- file.path(outs, "bloco6"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco6.txt"), split = TRUE)
cat("Bloco 6 —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d; ca <- L$ca
pop <- fread(file.path(base, "ibge_covariaveis/pop_uf_ano_sexo_idade.csv"))[tipo_faixa == "analise"]

# ================================================================ 1. Captura SIH × RBT
rbt <- fread(file.path(base, "rbt/rbt_coracao_uf.csv"))
rbt_ano <- fread(file.path(base, "rbt/rbt_coracao_ano.csv"))
sih <- d[ano %in% c(2020, 2023, 2024), .(SIH = .N, SIH_entrante = sum(entrante)), by = .(ano, uf = uf_hosp)]
cap <- merge(sih, rbt[, .(ano, uf, RBT = rbt_txc)], by = c("ano", "uf"), all = TRUE)
for (v in c("SIH", "SIH_entrante", "RBT")) set(cap, which(is.na(cap[[v]])), v, 0L)
cap <- merge(cap, unique(pop[, .(uf, regiao)]), by = "uf")
cap[, `:=`(dif_abs = SIH - RBT, captura_pct = fifelse(RBT > 0, 100 * SIH / RBT, NA_real_), pct_AIH_entrante = fifelse(SIH > 0, 100 * SIH_entrante / SIH, NA_real_))]
cap[, edicao_RBT := c(`2020` = "RBT 2020", `2023` = "RBT 2023", `2024` = "RBT 2024")[as.character(ano)]]
setorder(cap, ano, -RBT)
cap_reg <- cap[, .(SIH = sum(SIH), RBT = sum(RBT)), by = .(ano, regiao)][, captura_pct := 100 * SIH / RBT]
cap_nac <- merge(d[, .(SIH = .N), by = ano], rbt_ano[, .(ano, RBT = rbt_txc, fonte)], by = "ano")[, captura_pct := 100 * SIH / RBT]
cat("\n== Captura nacional por ano (série RBT: edição na coluna fonte)\n"); print(cap_nac)
cat("\n== Captura por UF (2020, 2023, 2024)\n"); print(cap)
cuf <- cap[, .(SIH = sum(SIH), RBT = sum(RBT)), by = uf][, captura_3anos := fifelse(RBT > 0, 100 * SIH / RBT, NA_real_)]
uf90 <- cuf[!is.na(captura_3anos) & captura_3anos >= 90, uf]
uf_fora <- setdiff(unique(d$uf_hosp), uf90)
cat("\nUFs com captura ≥90% (soma 2020+2023+2024):", paste(sort(uf90), collapse = ", "), "\nUFs de hospital excluídas na restrição:", paste(sort(uf_fora), collapse = ", "), "\n")
excl_carac <- merge(d[uf_hosp %in% uf_fora, .(AIH = .N, obitos = sum(morte), mort_pct = 100 * mean(morte), centros = uniqueN(centro), V_mediana = as.numeric(median(V))), by = uf_hosp],
                    cuf, by.x = "uf_hosp", by.y = "uf", all.x = TRUE)[order(-AIH)]
excl_carac[is.na(RBT), motivo := "sem registro no RBT 2020/2023/2024 (captura desconhecida)"][is.na(motivo), motivo := "captura < 90%"]
print(excl_carac)

# ================================================================ 2. Funil — antes das sensibilidades (define a exclusão post hoc)
fun <- d[, .(O = sum(morte), E = sum(p_risco), N = .N), by = centro][, OE := O / E]
lim <- function(E, p) { r <- qpois(p, E); a <- (ppois(r, E) - p) / (ppois(r, E) - ppois(r - 1, E)); pmax((r - a) / E, 0) }
fun[, `:=`(sup95 = lim(E, .975), sup998 = lim(E, .999), inf95 = lim(E, .025), inf998 = lim(E, .001))]
fora998 <- fun[OE > sup998, as.character(centro)]
cat("\n== Funil: centros acima de 99,8%:", length(fora998), "| abaixo de 0,2%:", fun[OE < inf998, .N],
    "| fora de 95% (acima/abaixo):", fun[OE > sup95, .N], "/", fun[OE < inf95, .N], "\n")
gE <- data.table(E = seq(0.3, max(fun$E) * 1.05, length.out = 400))[, `:=`(s95 = lim(E, .975), s998 = lim(E, .999), i95 = lim(E, .025), i998 = lim(E, .001))]
pf <- ggplot(fun, aes(E, OE)) + geom_hline(yintercept = 1, linewidth = 0.3) +
  geom_line(data = gE, aes(E, s95), linetype = "dashed", colour = "grey40") + geom_line(data = gE, aes(E, i95), linetype = "dashed", colour = "grey40") +
  geom_line(data = gE, aes(E, s998), colour = "grey40") + geom_line(data = gE, aes(E, i998), colour = "grey40") +
  geom_point(aes(size = N), shape = 21, fill = PAL[1], alpha = 0.6) + scale_size_area(max_size = 6, name = "AIH") +
  coord_cartesian(ylim = c(0, 4)) +
  labs(x = "Óbitos esperados (modelo: faixa etária, sexo, ano)", y = "Óbitos observados / esperados",
       title = paste0("Funil de óbito hospitalar por centro (", nlevels(d$centro), " centros, sem identificação)"),
       subtitle = "Tracejado = 95%; contínuo = 99,8%. Descritivo; sem ranking e sem leitura de qualidade") + tema
ggsave(file.path(out, "FiguraS6_funil.png"), pf, width = 8, height = 5.5, dpi = 200, bg = "white")

# ================================================================ 2b. Diagnóstico do modelo de risco
suppressPackageStartupMessages(library(pROC))
roc0 <- roc(d$morte, d$p_risco, quiet = TRUE); ci0 <- ci.auc(roc0, method = "delong")
risco_auc <- data.table(AUC = as.numeric(ci0[2]), lo = as.numeric(ci0[1]), hi = as.numeric(ci0[3]), metodo = "DeLong")
d[, decil := cut(rank(p_risco, ties.method = "first"), 10, labels = 1:10)]
risco_cal <- d[, .(n = .N, O = sum(morte), E = sum(p_risco)), by = decil][order(decil)][, `:=`(obs_pct = 100 * O / n, esp_pct = 100 * E / n)]
cat("\n== Modelo de risco C0: estatística C =", round(risco_auc$AUC, 3), "(", round(risco_auc$lo, 3), "–", round(risco_auc$hi, 3), ")\n"); print(risco_cal)

# ================================================================ 3. Sensibilidades do modelo de volume
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9)))
contr <- function(fit, x = NULL) {   # entre 5/40 vs 20; P10/P90 vs P50; dentro +10; † = valor fora da faixa observada de "entre" na amostra
  nb <- union(nomes_b(fit), c("e1", "e2")); mk <- function(v, r) { B <- rcs2(c(v, r), kE); z <- setNames(rep(0, length(nb)), nb); z[c("e1", "e2")] <- B[1, ] - B[2, ]; z }
  Lm <- rbind(mk(5, 20), mk(40, 20), mk(kE[1], kE[2]), mk(kE[3], kE[2])); zd <- setNames(rep(0, length(nb)), nb); zd["dentro10"] <- 1
  r <- or_contraste(fit, rbind(Lm, zd), c("Entre 5 vs 20", "Entre 40 vs 20", "Entre P10 vs P50", "Entre P90 vs P50", "Dentro +10 TxC/ano"))
  if (!is.null(x)) {
    rg <- range(x$entre); v <- list(c(5, 20), c(40, 20), kE[c(1, 2)], kE[c(3, 2)])
    fora <- sapply(v, function(z) any(z < rg[1] - 1e-9 | z > rg[2] + 1e-9))
    r[, fora_suporte := c(fora, FALSE)]
  } else r[, fora_suporte := FALSE]
  r
}
f_h1 <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
f_h1l <- morte ~ e1 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
prep <- function(x, entre_col = NULL) {
  x <- copy(x); x[, centro := droplevels(centro)]; x[, faixa5 := droplevels(faixa5)]
  if (is.null(entre_col)) { x[, entre := mean(Vm1), by = centro] } else x[, entre := get(entre_col)]
  x[, dentro10 := (Vm1 - entre) / 10]; add_rcs(x, "entre", kE, "e"); x
}
sens <- list()
roda_s <- function(rot, x, f = f_h1, fl = f_h1l, nota = "") {
  cat("\n--", rot, "\n"); fit <- escada(f, x, fl, rot)
  sens[[rot]] <<- contr(fit, x)[, `:=`(analise = rot, AIH = nrow(x), obitos = sum(x$morte), centros = uniqueN(x$centro), passo = fit$passo, nota = nota)]
}
roda_s("Principal (referência)", prep(d))
roda_s("Só adultos (≥18 anos)", prep(d[idade >= 18]))
roda_s("Sem 2020–2021", prep(d[!ano %in% 2020:2021]))
# V com o caso índice: translação de 1 unidade (com nós transladados) → modelo idêntico; demonstração numérica
xv <- copy(d); xv[, entreV := mean(V), by = centro]; xv[, dentro10 := (V - entreV) / 10]
bV <- rcs2(xv$entreV, kE + 1); xv[, `:=`(e1 = bV[, 1], e2 = bV[, 2])]
fV <- escada(f_h1, xv, f_h1l, "V com índice")
B0 <- rcs2(c(40, 20), kE); B1 <- rcs2(c(41, 21), kE + 1)
cat("V com índice: dentro idêntico (|dif| máx =", max(abs(xv$dentro10 - prep(d)$dentro10)), "); base do spline transladada idêntica até constante:",
    isTRUE(all.equal(B0[1, ] - B0[2, ], B1[1, ] - B1[2, ])), "\n")
sens[["V com índice (contínuo)"]] <- contr(list(m = fV$m), prep(d))[, `:=`(analise = "V com índice (contínuo; nós transladados +1)", AIH = nrow(xv), obitos = sum(xv$morte), centros = uniqueN(xv$centro), passo = fV$passo,
  nota = "Matematicamente idêntico ao V − 1 nos modelos contínuos; a diferença só aparece nas categorias de V (Tabela 4)")]
# volume defasado
lag <- ca[, .(centro, ano = ano + 1L, Vlag = n_txc)]
xl <- merge(d[ano > INI], lag, by.x = c("centro", "ano"), by.y = c("centro", "ano"), all.x = TRUE)[is.na(Vlag), Vlag := 0L]
xl[, centro := factor(centro)]; xl[, entreL := mean(Vlag), by = centro]; xl[, Vm1 := Vlag]   # para prep: dentro = Vlag − média
roda_s(sprintf("Volume defasado (ano anterior; sem %d)", INI), prep(xl, "entreL"), nota = "Exposição = TxC do centro no ano anterior")
# média só nos anos ativos (sem zeros intermediários) e com zeros do período ativo
cy <- ca[, .(centro, ano, n_txc)]
per_at <- cy[n_txc > 0, .(a0 = min(ano), a1 = max(ano)), by = centro]
cy <- merge(cy, per_at, by = "centro")[ano >= a0 & ano <= a1]
m_at <- cy[n_txc > 0, .(entre_at = mean(n_txc) - 1), by = centro]; m_z <- cy[, .(entre_z = mean(n_txc) - 1), by = centro]
xa <- merge(merge(d, m_at, by.x = "centro", by.y = "centro"), m_z, by = "centro"); xa[, centro := factor(centro)]
cat("Centros com zero intermediário:", cy[n_txc == 0, uniqueN(centro)], "\n")
roda_s("Entre = média simples dos anos ativos (sem zeros)", prep(xa, "entre_at"))
roda_s("Entre = média do período ativo (com zeros intermediários)", prep(xa, "entre_z"))
roda_s(paste0("Sem os 2 primeiros anos dos centros com 1º TxC ≥", ENT), prep(d[!(entrante & ano_programa <= 2)]))
if (length(fora998)) roda_s(paste0("Sem centro(s) acima de 99,8% no funil (post hoc; n = ", length(fora998), ")"), prep(d[!centro %in% fora998]),
                            nota = "Exclusão decidida após o funil (post hoc)")
rep_ids <- d[, .N, by = paciente_provavel_id][N > 1, paciente_provavel_id]
roda_s(sprintf("Sem os %d AIH de prováveis readmitidos", d[paciente_provavel_id %in% rep_ids, .N]), prep(d[!paciente_provavel_id %in% rep_ids]))
xp <- d[order(paciente_provavel_id, ano, mes_inter, id_aih)][, morte_pac := max(morte), by = paciente_provavel_id][, .SD[1], by = paciente_provavel_id][, morte := morte_pac]
roda_s("Uma linha por paciente (1ª AIH; óbito em qualquer AIH)", prep(xp))
roda_s("UFs com captura SIH/RBT ≥90%", prep(d[uf_hosp %in% uf90]), nota = paste("UFs:", paste(sort(uf90), collapse = ", ")))
xf <- prep(d); xf[, ano_f := factor(ano)]
roda_s("Ano como efeito fixo (fator)", xf, morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + ano_f + (1 | centro), morte ~ e1 + dentro10 + faixa5 + sexoF + ano_f + (1 | centro))
# efeito fixo de centro (logística condicional) — só o termo dentro
xc <- prep(d)
cl <- tryCatch(clogit(morte ~ dentro10 + faixa5 + sexoF + a1 + a2 + strata(centro), data = xc, method = "exact"), error = function(e) NULL)
met <- "exata"
if (is.null(cl)) { cl <- clogit(morte ~ dentro10 + faixa5 + sexoF + a1 + a2 + strata(centro), data = xc, method = "efron"); met <- "Efron" }
bc <- coef(cl)["dentro10"]; sc <- sqrt(vcov(cl)["dentro10", "dentro10"])
sens[["clogit"]] <- data.table(contraste = "Dentro +10 TxC/ano", OR = exp(bc), lo = exp(bc - 1.96 * sc), hi = exp(bc + 1.96 * sc), p = 2 * pnorm(-abs(bc / sc)),
  analise = paste0("Efeito fixo de centro (logística condicional, verossimilhança ", met, ")"), AIH = nrow(xc), obitos = sum(xc$morte), centros = uniqueN(xc$centro), passo = NA_integer_, nota = "")
# Chagas com Firth (sem efeito de centro), comparado ao Firth sem Chagas
cat("\n-- Firth com e sem Chagas\n")
fF0 <- logistf(morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2, data = as.data.frame(xc), pl = FALSE)
fF1 <- logistf(morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + chagas_qualquer, data = as.data.frame(xc), pl = FALSE)
for (nm in c("Firth sem Chagas (sem efeito de centro)", "Firth com Chagas (sem efeito de centro)")) {
  ff <- if (grepl("com", nm)) fF1 else fF0
  sens[[nm]] <- contr(list(m = ff, vc = vcov(ff)), xc)[, `:=`(analise = nm, AIH = nrow(xc), obitos = sum(xc$morte), centros = uniqueN(xc$centro), passo = NA_integer_, nota = "")]
}
chg <- data.table(termo = "Chagas", OR = exp(coef(fF1)["chagas_qualquer"]), lo = exp(confint(fF1)["chagas_qualquer", 1]), hi = exp(confint(fF1)["chagas_qualquer", 2]),
                  AIH_chagas = sum(xc$chagas_qualquer), obitos_chagas = sum(xc$morte[xc$chagas_qualquer == 1]))
print(chg)
if (INI < 2008) {   # sensibilidades da junção das duas tabelas de procedimentos (antiga até 2007, SIGTAP desde 2008)
  roda_s("Só 2008–2025 (tabela SIGTAP)", prep(d[ano >= 2008]))
  roda_s(sprintf("Sem %d–%d (diagnóstico principal quase sempre Z94)", INI, INI + 1), prep(d[ano >= INI + 2]))
  roda_s("Sem AIH com hospital identificado por troca de identificador (regra 3 CNPJ→CNES)", prep(d[regra_cnes != "3_troca_identificador"]),
         nota = paste("Excluídas:", d[regra_cnes == "3_troca_identificador", .N], "AIH"))
  xs <- prep(d); xs[, sigtap := as.integer(ano >= 2008)]
  roda_s("Com indicador de tabela SIGTAP (2008+)", xs, update(f_h1, . ~ . + sigtap), update(f_h1l, . ~ . + sigtap))
}
S <- rbindlist(sens, use.names = TRUE, fill = TRUE)
cat("\n== Sensibilidades do H1\n"); print(S[, .(analise, contraste, OR = round(OR, 3), lo = round(lo, 3), hi = round(hi, 3), AIH, obitos, passo)])
S[is.na(fora_suporte), fora_suporte := FALSE]
TabS <- dcast(S[, .(analise, AIH, obitos, centros, passo, contraste, v = paste0(ic(OR, lo, hi), fifelse(fora_suporte, " †", "")))], analise + AIH + obitos + centros + passo ~ contraste, value.var = "v")
TabS[, ord := match(analise, unique(S$analise))]; setorder(TabS, ord); TabS[, ord := NULL]

# ================================================================ 4. Pandemia
ms <- CJ(ano = 2015:2025, mes = 1:12)
ms <- merge(ms, d[, .(n = .N), by = .(ano, mes = mes_inter)], all.x = TRUE)[is.na(n), n := 0L]
ms[, `:=`(t = seq_len(.N), data = as.Date(sprintf("%d-%02d-01", ano, mes)))]
ms[, `:=`(degrau = as.integer(data >= as.Date("2020-03-01")), s1 = sin(2 * pi * mes / 12), c1 = cos(2 * pi * mes / 12))]
ms[, t_pos := pmax(0, t - ms[data == as.Date("2020-03-01"), t] + 1) * degrau]
qp <- glm(n ~ t + s1 + c1 + degrau + t_pos, family = quasipoisson, data = ms)
cat("\n== Pandemia: quasi-Poisson; dispersão =", round(summary(qp)$dispersion, 2), "\n"); print(round(coef(summary(qp)), 4))
cf <- copy(ms)[, `:=`(degrau = 0L, t_pos = 0)]
ms[, `:=`(ajust = fitted(qp), contraf = predict(qp, cf, type = "response"))]
B <- MASS::mvrnorm(5000, coef(qp), vcov(qp)); Xc <- model.matrix(~ t + s1 + c1 + degrau + t_pos, cf)
janela <- ms$data >= as.Date("2020-03-01") & ms$data <= as.Date("2021-12-01")
esp <- colSums(exp(Xc[janela, ] %*% t(B))); obs <- sum(ms$n[janela])
pand <- data.table(janela = "mar/2020–dez/2021", observado = obs, esperado = sum(ms$contraf[janela]), esp_lo = quantile(esp, .025), esp_hi = quantile(esp, .975),
                   deficit = obs - sum(ms$contraf[janela]), def_lo = obs - quantile(esp, .975), def_hi = obs - quantile(esp, .025),
                   RR_degrau = exp(coef(qp)["degrau"]), RR_lo = exp(confint.default(qp)["degrau", 1]), RR_hi = exp(confint.default(qp)["degrau", 2]))
print(pand)
pp <- ggplot(ms, aes(data)) + geom_col(aes(y = n), fill = "grey75", width = 25) + geom_line(aes(y = ajust), colour = PAL[1]) +
  geom_line(data = ms[data >= as.Date("2020-03-01")], aes(y = contraf), colour = PAL[2], linetype = "dashed") +
  geom_vline(xintercept = as.Date("2020-03-01"), linetype = "dotted") +
  labs(x = NULL, y = "Transplantes por mês (AIH)", title = "Transplantes cardíacos no SIH por mês, 2015–2025",
       subtitle = "Azul = modelo quasi-Poisson ajustado; vermelho tracejado = contrafactual sem mudança em mar/2020") + tema
ggsave(file.path(out, "FiguraS6_pandemia.png"), pp, width = 9, height = 4, dpi = 200, bg = "white")

# ================================================================ 5. Tendência da mortalidade
cat("\n== Tendência temporal da mortalidade\n")
d[, ano_f := factor(ano)]; d[, ano_c := (ano - 2016) / 5]
tL <- escada(morte ~ ano_c + faixa5 + sexoF + (1 | centro), d, NULL, "ano linear")
tS <- escada(morte ~ a1 + a2 + faixa5 + sexoF + (1 | centro), d, NULL, "ano spline")
tF <- escada(morte ~ ano_f + faixa5 + sexoF + (1 | centro), d, NULL, "ano fator")
todos_glmer <- all(sapply(list(tL, tS, tF), function(f) inherits(f$m, "glmerMod")))
cat("Modelos da tendência no multinível:", todos_glmer, "\n")
ll_df <- function(f) c(ll = as.numeric(logLik(f$m)), df = if (inherits(f$m, "glmerMod")) attr(logLik(f$m), "df") else length(coef(f$m)))
ano_or <- or_tab(tF, grep("ano_f", nomes_b(tF), value = TRUE))[, ano := as.integer(sub("ano_f", "", termo))]
cp_ll <- function(x, k) as.numeric(logLik(glm(morte ~ faixa5 + sexoF + ano + I(pmax(ano - k, 0)), family = binomial, data = x)))
ks <- (INI + 2):2023
ll <- sapply(ks, function(k) cp_ll(d, k)); k_hat <- ks[which.max(ll)]
cls <- split(seq_len(nrow(d)), d$centro)
B_cp <- as.integer(Sys.getenv("B_BOOT", "1000"))   # 1000 na análise; valor menor só para teste rápido
kb <- replicate(B_cp, { s <- sample(names(cls), length(cls), replace = TRUE); x <- d[unlist(cls[s])]; ks[which.max(sapply(ks, function(k) cp_ll(x, k)))] })
g_cp <- glm(morte ~ faixa5 + sexoF + ano + I(pmax(ano - k_hat, 0)), family = binomial, data = d)
cpt <- data.table(B_bootstrap = length(kb), quebra = k_hat, IC_lo = quantile(kb, .025), IC_hi = quantile(kb, .975),
                  OR_ano_antes = exp(coef(g_cp)["ano"]), OR_ano_depois = exp(sum(coef(g_cp)[c("ano", paste0("I(pmax(ano - k_hat, 0))"))])),
                  LR_vs_linear = 2 * (max(ll) - as.numeric(logLik(glm(morte ~ faixa5 + sexoF + ano, family = binomial, data = d)))))
cat("Ponto de mudança:\n"); print(cpt); print(table(kb))
tend <- rbindlist(lapply(list(list("Spline natural (2 gl) vs ano linear", tS), list("Ano como fator vs ano linear", tF)), function(z) {
  a <- ll_df(tL); b <- ll_df(z[[2]]); x <- 2 * (b[["ll"]] - a[["ll"]]); g <- b[["df"]] - a[["df"]]
  data.table(teste = z[[1]], chisq = x, gl = g, p = pchisq(x, g, lower.tail = FALSE),
             nota = if (todos_glmer) "multinível" else "ATENÇÃO: modelos de famílias diferentes (escada); LRT não interpretável")
}))
print(tend)
cp2 <- NULL; deg08 <- NULL
if (INI < 2008) {   # 2 quebras (exploratório) e degrau na troca de tabela (2008)
  cat("\n== Modelo com 2 quebras (exploratório) e degrau em 2008\n")
  ll0 <- as.numeric(logLik(glm(morte ~ faixa5 + sexoF + ano, family = binomial, data = d)))
  cp2_ll <- function(x, k1, k2) as.numeric(logLik(glm(morte ~ faixa5 + sexoF + ano + I(pmax(ano - k1, 0)) + I(pmax(ano - k2, 0)), family = binomial, data = x)))
  pares <- CJ(k1 = ks, k2 = ks)[k2 >= k1 + 3]
  pares[, ll := mapply(function(a, b) cp2_ll(d, a, b), k1, k2)]
  best <- pares[which.max(ll)]
  g2 <- glm(morte ~ faixa5 + sexoF + ano + I(pmax(ano - best$k1, 0)) + I(pmax(ano - best$k2, 0)), family = binomial, data = d)
  V2 <- vcovCL(g2, cluster = d$centro); b2 <- coef(g2); nm2 <- names(b2)[grep("ano", names(b2))]
  segOR <- function(w) { L <- setNames(rep(0, length(b2)), names(b2)); L[nm2[seq_along(w)]] <- w; e <- sum(L * b2); se <- sqrt(drop(t(L) %*% V2 %*% L))
    c(OR = exp(e), lo = exp(e - 1.96 * se), hi = exp(e + 1.96 * se), p = 2 * pnorm(-abs(e / se))) }
  B2 <- as.integer(Sys.getenv("B_BOOT2", "200"))
  kb2 <- t(replicate(B2, { s <- sample(names(cls), length(cls), replace = TRUE); x <- d[unlist(cls[s])]
    v <- pares[, mapply(function(a, b) cp2_ll(x, a, b), k1, k2)]; unlist(pares[which.max(v), .(k1, k2)]) }))
  n_par <- c(linear = 1, uma = 2, duas = 3)
  cp2 <- data.table(modelo = c("Linear", sprintf("1 quebra (%d)", k_hat), sprintf("2 quebras (%d, %d)", best$k1, best$k2)),
                    logLik = c(ll0, max(ll), best$ll), parametros_tempo = n_par)
  cp2[, dBIC := (-2 * logLik + log(nrow(d)) * parametros_tempo) - min(-2 * logLik + log(nrow(d)) * parametros_tempo)]   # demais termos iguais nos 3 modelos
  cp2[, LR_vs_anterior := c(NA, 2 * diff(logLik))]
  seg <- rbind(data.table(segmento = sprintf("%d–%d", INI, best$k1), t(segOR(1))), data.table(segmento = sprintf("%d–%d", best$k1, best$k2), t(segOR(c(1, 1)))),
               data.table(segmento = sprintf("%d–2025", best$k2), t(segOR(c(1, 1, 1)))))
  cp2 <- list(modelos = cp2, segmentos = seg,
              bootstrap = data.table(B = B2, k1_lo = quantile(kb2[, 1], .025), k1_hi = quantile(kb2[, 1], .975),
                                     k2_lo = quantile(kb2[, 2], .025), k2_hi = quantile(kb2[, 2], .975),
                                     pct_mesmo_par = 100 * mean(kb2[, 1] == best$k1 & kb2[, 2] == best$k2)))
  print(cp2)
  # degrau na troca de tabela: indicador 2008+ no modelo de tendência principal (spline de 2 gl) e no de 2 quebras
  d[, sigtap := as.integer(ano >= 2008)]
  tD <- escada(morte ~ a1 + a2 + sigtap + faixa5 + sexoF + (1 | centro), d, NULL, "ano spline + degrau 2008")
  gD <- glm(morte ~ faixa5 + sexoF + ano + I(pmax(ano - best$k1, 0)) + I(pmax(ano - best$k2, 0)) + sigtap, family = binomial, data = d)
  vD <- vcovCL(gD, cluster = d$centro)
  deg08 <- rbind(or_tab(tD, "sigtap")[, modelo := "Multinível: ano spline (2 gl) + indicador 2008+"],
                 data.table(termo = "sigtap", OR = exp(coef(gD)["sigtap"]), lo = exp(coef(gD)["sigtap"] - 1.96 * sqrt(vD["sigtap", "sigtap"])),
                            hi = exp(coef(gD)["sigtap"] + 1.96 * sqrt(vD["sigtap", "sigtap"])), p = 2 * pnorm(-abs(coef(gD)["sigtap"] / sqrt(vD["sigtap", "sigtap"]))),
                            modelo = "Logística com 2 quebras + indicador 2008+ (EP por centro)"))
  print(deg08)
}

# ================================================================ 6. Reembolso
ree <- rbind(d[, .(grupo = "Ano", nivel = as.character(ano), n = .N, mediana = median(val_tot_real_dez2025), P25 = quantile(val_tot_real_dez2025, .25), P75 = quantile(val_tot_real_dez2025, .75)), by = ano][, ano := NULL],
             d[, .(grupo = "Região do hospital", n = .N, mediana = median(val_tot_real_dez2025), P25 = quantile(val_tot_real_dez2025, .25), P75 = quantile(val_tot_real_dez2025, .75)), by = .(nivel = regiao_hosp)],
             d[, .(grupo = "Tipo de centro", n = .N, mediana = median(val_tot_real_dez2025), P25 = quantile(val_tot_real_dez2025, .25), P75 = quantile(val_tot_real_dez2025, .75)), by = .(nivel = fifelse(entrante, LAB_ENT, LAB_INC))])
print(ree)
pr <- ggplot(ree[grupo == "Ano"], aes(as.integer(nivel), mediana / 1000)) + geom_ribbon(aes(ymin = P25 / 1000, ymax = P75 / 1000), fill = "grey85") +
  geom_line() + geom_point() + geom_text(aes(y = P75 / 1000, label = n), vjust = -0.5, size = 2.4) +
  labs(x = "Ano", y = "R$ mil (dez/2025)", title = "Valor total real por AIH de transplante cardíaco (IPCA, R$ de dez/2025)",
       subtitle = "Linha = mediana; faixa = P25–P75; números = AIH. Descritivo; sem relação com desfecho") + tema
ggsave(file.path(out, "FiguraS6_reembolso.png"), pr, width = 8, height = 4, dpi = 200, bg = "white")

# ================================================================ saída
fwrite(TabS, file.path(out, "TabelaS6_sensibilidades.csv"), bom = TRUE)
fwrite(cap, file.path(out, "TabelaS6_captura_UF.csv"), bom = TRUE)
salva_xlsx(c(list(Sensibilidades = TabS, Sensibilidades_longo = S, Chagas_Firth = chg, Captura_UF = cap, Captura_regiao = cap_reg, Captura_nacional = cap_nac,
                Captura_3anos_UF = cuf, UFs_excluidas = excl_carac, Funil = fun, Pandemia_mensal = ms, Pandemia_deficit = pand,
                Tendencia_testes = tend, Tendencia_ano_OR = ano_or, Ponto_mudanca = cpt, Reembolso = ree,
                Risco_AUC = risco_auc, Risco_calibracao = risco_cal),
             if (!is.null(cp2)) list(Duas_quebras_modelos = cp2$modelos, Duas_quebras_segmentos = cp2$segmentos,
                                     Duas_quebras_bootstrap = cp2$bootstrap, Degrau_2008 = deg08)),
           file.path(out, "Bloco6_tabelas.xlsx"))
cat("\nArquivos:", paste(list.files(out), collapse = ", "), "\n")
sink()
