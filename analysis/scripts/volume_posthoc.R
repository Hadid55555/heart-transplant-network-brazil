# Análises post hoc do modelo de volume (mesmo preparo, escada de convergência e ajuste dos blocos 3 e 4):
#  R1  termo "dentro" com tendência de ano própria de cada centro (random slope de ano por centro)
#  R2  curva "entre" em escala de OR vs P50 (Figura 3A)
#  R3  5 primeiros casos dos centros novos segundo a janela de observação inicial (2000–2001 e 2000–2003)
# Uso: LANG=C.UTF-8 TXC_INI=2000 Rscript scripts/volume_posthoc.R data_2000 outputs_2000_2025/sensibilidade
args <- commandArgs(trailingOnly = TRUE)
base <- args[1]; out <- args[2]
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_volume_posthoc.txt"), split = TRUE)
cat("Volume (post hoc) —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9)))
add_rcs(d, "entre", kE, "e")
d[, anoc := (ano_inter - 2012.5) / 10]   # ano centrado, por década (escala numérica do random slope)

f_main <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
f_rs   <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 + anoc | centro)
f_rs0  <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro) + (0 + anoc | centro)

cat("\n== Modelo principal (reprodução)\n"); fit0 <- escada(f_main, d, NULL, "R1 principal")
cat("\n== Random slope de ano por centro (correlacionado)\n"); fit1 <- escada(f_rs, d, NULL, "R1 random slope")
cat("\n== Random slope de ano por centro (sem correlação)\n"); fit2 <- escada(f_rs0, d, NULL, "R1 random slope sem correlação")

nb <- nomes_b(fit0); Ld <- matrix(0, 1, length(nb), dimnames = list(NULL, nb)); Ld[, "dentro10"] <- 1
dentro <- rbindlist(lapply(list(`Principal (intercepto aleatório)` = fit0, `Random slope de ano por centro` = fit1,
                                `Random slope sem correlação` = fit2), function(f) {
  if (is.null(f$m)) return(data.table(OR = NA_real_, lo = NA_real_, hi = NA_real_, p = NA_real_, passo = NA_integer_))
  r <- or_tab(f, "dentro10"); r[, passo := f$passo]; r[, .(OR, lo, hi, p, passo)] }), idcol = "modelo")
lrt_rs <- if (inherits(fit1$m, "glmerMod") && inherits(fit0$m, "glmerMod")) anova(fit0$m, fit1$m) else NULL
if (!is.null(lrt_rs)) dentro[, LRT_random_slope := sprintf("χ² = %.2f (2 gl), p = %.3g", lrt_rs$Chisq[2], lrt_rs$`Pr(>Chisq)`[2])]
if (inherits(fit1$m, "glmerMod")) { vc <- as.data.frame(VarCorr(fit1$m)); print(vc) }
cat("\nTermo 'dentro' (+10 TxC/ano acima da média do centro):\n"); print(dentro)

# R1b: random slope também com o teste global de 'entre'
lrt_entre_rs <- if (inherits(fit1$m, "glmerMod")) anova(update(fit1$m, . ~ . - e1 - e2), fit1$m) else NULL
if (!is.null(lrt_entre_rs)) cat(sprintf("LRT 'entre' com random slope (2 gl): χ² = %.2f, p = %.3g\n", lrt_entre_rs$Chisq[2], lrt_entre_rs$`Pr(>Chisq)`[2]))

# ---------------------------------------------------------------- R2: curva 'entre' como OR vs P50
grid <- seq(0, ceiling(max(d$entre) * 10) / 10, by = 0.5); grid <- grid[grid <= max(d$entre)]
Lc <- do.call(rbind, lapply(grid, function(v) { B <- rcs2(c(v, kE[2]), kE); z <- setNames(rep(0, length(nb)), nb); z[c("e1", "e2")] <- B[1, ] - B[2, ]; z }))
curva <- or_contraste(fit0, Lc, sprintf("%.1f", grid)); curva[, entre := grid]
curva[, n_centros_ate := sapply(grid, function(v) uniqueN(d[entre <= v + 1e-9, centro]))]
fwrite(curva[, .(entre, OR, lo, hi)], file.path(out, "curva_entre_OR_vs_P50.csv"))
p10 <- curva[which.min(abs(entre - kE[1]))]
cat(sprintf("\nP10 (%.1f) vs P50 (%.1f): OR %.2f (%.2f–%.2f)\n", kE[1], kE[2], p10$OR, p10$lo, p10$hi))

# ---------------------------------------------------------------- R3: 5 primeiros com janela 2000–2003
prim <- d[, .(ano1 = min(ano_inter)), by = centro]
d <- merge(d, prim, by = "centro")
F <- function(term) as.formula(paste("morte ~", term, "+ faixa5 + sexoF + a1 + a2 + (1 | centro)"))
cinco <- function(corte, rot) {
  e <- d[ano1 >= corte]; setorder(e, centro, ano_inter, mes_inter, id_aih); e[, seq := seq_len(.N), by = centro]
  e[, primeiros5 := as.integer(seq <= 5)]
  f <- escada(F("primeiros5"), e, NULL, rot)
  r <- or_tab(f, "primeiros5")
  r[, .(definicao = rot, centros = uniqueN(e$centro), AIH = nrow(e), obitos = sum(e$morte),
        AIH_5prim = sum(e$primeiros5), obitos_5prim = sum(e$morte[e$primeiros5 == 1]), OR, lo, hi, p, passo = f$passo)]
}
r3 <- rbind(cinco(2002, "Sensibilidade: 1º TxC observado ≥2002 (janela 2000–2001)"),
            cinco(2004, "Principal: 1º TxC observado ≥2004 (janela 2000–2003)"))
cat("\n5 primeiros casos:\n"); print(r3)

# reconciliação: centros 'novos' de 2002–2003 que já existiam? anos sem TxC entre o 1º e o último ano dos incumbentes
gaps <- d[, .(anos_ativos = uniqueN(ano_inter), ano1 = min(ano_inter), anoN = max(ano_inter)), by = centro]
gaps[, anos_sem_txc_no_periodo := (anoN - ano1 + 1) - anos_ativos]
fwrite(gaps[order(ano1)][, .(ano1, anoN, anos_ativos, anos_sem_txc_no_periodo)], file.path(out, "centros_lacunas_anonimo.csv"))

fwrite(dentro, file.path(out, "R1_dentro_random_slope.csv")); fwrite(r3, file.path(out, "R3_cinco_primeiros_janela.csv"))
sink()
