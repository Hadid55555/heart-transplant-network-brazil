# Post hoc: a conclusão principal do modelo de volume se mantém ao retirar cada centro?
# Para cada reajuste leave-one-centre-out do modelo principal: LRT global de "entre" (2 gl), LRT de não
# linearidade (1 gl) e OR de "dentro". Mesma base de spline e mesmos nós do modelo principal (como no LOCO do bloco 3).
# Uso: LANG=C.UTF-8 Rscript scripts/loco_lrt.R data_2000_w04 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; outs <- if (length(args) >= 2) args[2] else "outputs"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
L <- carrega(base); d <- L$d
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9))); add_rcs(d, "entre", kE, "e")
f_main <- morte ~ e1 + e2 + dentro10 + faixa5 + sexoF + a1 + a2 + (1 | centro)
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
lrt <- function(x) {
  r <- .fit_g(f_main, x, ctl); if (is.null(r$m)) return(NULL); m <- r$m
  m0 <- update(m, . ~ . - e1 - e2); m1 <- update(m, . ~ . - e2)
  g <- anova(m0, m); n <- anova(m1, m); b <- fixef(m)["dentro10"]; se <- sqrt(vcov(m)["dentro10", "dentro10"])
  data.table(chi2_entre = g$Chisq[2], p_entre = g$`Pr(>Chisq)`[2], p_nao_linear = n$`Pr(>Chisq)`[2],
             OR_dentro = exp(b), lo_dentro = exp(b - 1.96 * se), hi_dentro = exp(b + 1.96 * se), avisos = length(r$msgs))
}
ref <- lrt(d)[, analise := sprintf("Todos os %d centros (principal)", nlevels(d$centro))]
tam <- d[, .N, by = centro]; maior <- tam[which.max(N), as.character(centro)]
loco <- rbindlist(lapply(levels(d$centro), function(cc) {
  x <- d[centro != cc]; x[, centro := droplevels(centro)]
  o <- lrt(x); if (is.null(o)) return(NULL)
  o[, `:=`(sem_maior = cc == maior, AIH_retiradas = tam[centro == cc, N])]
}))
res <- rbind(
  ref[, .(analise, reajustes = 1L, p_entre_min = p_entre, p_entre_max = p_entre, n_p_menor_005 = as.integer(p_entre < 0.05),
          p_nl_min = p_nao_linear, p_nl_max = p_nao_linear, OR_dentro_min = OR_dentro, OR_dentro_max = OR_dentro,
          n_IC_dentro_exclui_1 = as.integer(lo_dentro > 1 | hi_dentro < 1), avisos = avisos)],
  loco[, .(analise = sprintf("Leave-one-centre-out (%d reajustes)", nrow(loco)), reajustes = .N, p_entre_min = min(p_entre), p_entre_max = max(p_entre),
           n_p_menor_005 = sum(p_entre < 0.05), p_nl_min = min(p_nao_linear), p_nl_max = max(p_nao_linear),
           OR_dentro_min = min(OR_dentro), OR_dentro_max = max(OR_dentro), n_IC_dentro_exclui_1 = sum(lo_dentro > 1 | hi_dentro < 1), avisos = sum(avisos > 0))],
  loco[(sem_maior), .(analise = "Sem o maior centro", reajustes = .N, p_entre_min = p_entre, p_entre_max = p_entre, n_p_menor_005 = as.integer(p_entre < 0.05),
                      p_nl_min = p_nao_linear, p_nl_max = p_nao_linear, OR_dentro_min = OR_dentro, OR_dentro_max = OR_dentro,
                      n_IC_dentro_exclui_1 = as.integer(lo_dentro > 1 | hi_dentro < 1), avisos = avisos)])
print(res)
cat("\nReajustes com p de 'entre' < 0,05: AIH retiradas =", paste(loco[p_entre < 0.05, AIH_retiradas], collapse = ", "), "\n")
dir.create(file.path(outs, "bloco7"), showWarnings = FALSE)
fwrite(res, file.path(outs, "bloco7/R13_loco_lrt.csv"))
fwrite(loco[, .(AIH_retiradas, sem_maior, chi2_entre, p_entre, p_nao_linear, OR_dentro, lo_dentro, hi_dentro, avisos)][order(p_entre)],
       file.path(outs, "_local/R13_loco_lrt_por_reajuste.csv"))   # sem rótulo de centro; fora do Git por cautela
