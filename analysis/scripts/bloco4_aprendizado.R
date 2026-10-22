# Bloco 4 — Primeiros casos dos centros novos (exploratório)
# Uso: LANG=C.UTF-8 Rscript scripts/bloco4_aprendizado.R data_2000_w04 outputs_2000_2025/bloco4
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; out <- if (length(args) >= 2) args[2] else "outputs/bloco4"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco4.txt"), split = TRUE)
cat("Bloco 4 —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d
e <- d[(entrante)]; e[, centro := droplevels(centro)]
NE <- uniqueN(e$centro); DOM <- e[, .N, by = centro][which.max(N), as.character(centro)]   # maior centro novo
cat(sprintf("Maior centro entrante: %s (%.1f%% das AIH de entrantes)\n", DOM, 100 * e[centro == DOM, .N] / nrow(e)))
e[, primeiros5 := as.integer(seq <= 5)]
e[, cat_seq := factor(cut(seq, c(0, 5, 20, 50, Inf), labels = c("1-5", "6-20", "21-50", ">50")), levels = c(">50", "1-5", "6-20", "21-50"))]
e[, bloco := factor(cut(seq, c(0, 5, 10, 15, 20, Inf), labels = c("1-5", "6-10", "11-15", "16-20", ">20")), levels = c(">20", "1-5", "6-10", "11-15", "16-20"))]
e[, idade_prog := factor(cut(ano_programa, c(0, 4, 9, Inf), labels = c("<5", "5-9", ">=10")), levels = c(">=10", "<5", "5-9"))]
e[, log2seq := log2(seq)]
kS <- as.numeric(quantile(e$seq, c(.1, .5, .9))) / 10   # base em (nº do caso)/10, só para condicionamento numérico
e[, seq10 := seq / 10]; add_rcs(e, "seq10", kS, "s")
tam <- e[, .(n = .N, ob = sum(morte)), by = centro]
cat(sprintf("Entrantes: %d centros, %d AIH, %d óbitos; AIH/centro mediana %.0f; centros com ≥20 AIH: %d; sem óbito: %d\n",
            NE, nrow(e), sum(e$morte), median(tam$n), sum(tam$n >= 20), sum(tam$ob == 0)))
cat("Óbitos por faixa etária (entrantes):\n"); print(e[, .(n = .N, ob = sum(morte)), by = faixa5][order(faixa5)])

aj <- "+ faixa5 + sexoF + a1 + a2 + (1 | centro)"
F <- function(x) as.formula(paste("morte ~", x, aj))
roda <- function(dat, rot) {
  cat("\n==", rot, "\n")
  list(
    prim  = escada(F("primeiros5"), dat, NULL, paste(rot, "| primário: 5 primeiros")),
    rcs   = escada(F("s1 + s2"), dat, F("s1"), paste(rot, "| spline nº do caso")),
    log   = escada(F("log2seq"), dat, NULL, paste(rot, "| log2 nº do caso")),
    cat   = escada(F("cat_seq"), dat, NULL, paste(rot, "| categorias")),
    idade = escada(F("idade_prog"), dat, NULL, paste(rot, "| idade do programa")),
    bloco = escada(F("bloco"), dat, NULL, paste(rot, "| blocos de 5")))
}
resume <- function(fs, rot) {
  b <- setNames(rep(0, length(union(nomes_b(fs$rcs), c("s1", "s2")))), union(nomes_b(fs$rcs), c("s1", "s2"))); Lr <- t(sapply(c(1, 5, 10, 20), function(v) { B <- rcs2(c(v, 50) / 10, kS); z <- setNames(rep(0, length(b)), names(b)); z[c("s1", "s2")] <- B[1, ] - B[2, ]; z }))
  rbindlist(list(
    or_tab(fs$prim, "primeiros5")[, .(analise = "Primário: um dos 5 primeiros casos (vs demais)", termo = "5 primeiros", OR, lo, hi, p)],
    or_contraste(fs$rcs, Lr, paste0("caso ", c(1, 5, 10, 20), " vs caso 50"))[, .(analise = "Spline do nº do caso", termo = contraste, OR, lo, hi, p)],
    or_tab(fs$log, "log2seq")[, .(analise = "log2(nº do caso)", termo = "por duplicação do nº do caso", OR, lo, hi, p)],
    or_tab(fs$cat, grep("cat_seq", nomes_b(fs$cat), value = TRUE))[, .(analise = "Categorias (ref. >50)", termo = sub("cat_seq", "", termo), OR, lo, hi, p)],
    or_tab(fs$idade, grep("idade_prog", nomes_b(fs$idade), value = TRUE))[, .(analise = "Idade do programa (ref. ≥10 anos)", termo = sub("idade_prog", "", termo), OR, lo, hi, p)],
    or_tab(fs$bloco, grep("bloco", nomes_b(fs$bloco), value = TRUE))[, .(analise = "Blocos de 5 (ref. >20)", termo = sub("bloco", "", termo), OR, lo, hi, p)]
  ))[, amostra := rot][, passo := c(fs$prim$passo, rep(fs$rcs$passo, 4), fs$log$passo, rep(fs$cat$passo, 3), rep(fs$idade$passo, 2), rep(fs$bloco$passo, 4))]
}
fa <- roda(e, sprintf("Todos os %d centros", NE))
e5 <- e[centro != DOM]; e5[, centro := droplevels(centro)]
fs5 <- roda(e5, sprintf("Sem o %s", DOM))
A_TODOS <- sprintf("%d centros", NE); A_SEM <- sprintf("Sem %s", DOM)
res <- rbind(resume(fa, A_TODOS), resume(fs5, A_SEM))
print(res[, .(amostra, analise, termo, OR = round(OR, 2), lo = round(lo, 2), hi = round(hi, 2), p = signif(p, 3), passo)])

# brms se o modelo sem o maior centro novo não convergir até o passo 2
bayes <- NULL
if (fs5$prim$passo > 2) {
  cat("\nPrimário sem o", DOM, "não convergiu até o passo 2 → brms (priors D3)\n")
  suppressPackageStartupMessages(library(brms))
  pri <- c(prior(normal(0, 1), class = "b"), prior(student_t(3, 0, 2.5), class = "Intercept"), prior(normal(0, 1), class = "sd"))
  bm <- brm(morte ~ primeiros5 + faixa5 + sexoF + a1 + a2 + (1 | centro), data = e5, family = bernoulli(), prior = pri,
            chains = 4, iter = 2000, warmup = 1000, seed = 20261013, control = list(adapt_delta = 0.95), refresh = 0)
  s <- posterior_summary(bm, variable = "b_primeiros5", probs = c(.025, .5, .975))
  bayes <- data.table(analise = paste("brms sem", DOM), OR = exp(s[, "Q50"]), lo = exp(s[, "Q2.5"]), hi = exp(s[, "Q97.5"]),
                      Rhat = rhat(bm)["b_primeiros5"], div = sum(nuts_params(bm)[nuts_params(bm)$Parameter == "divergent__", "Value"]))
  print(bayes)
} else cat("\nPrimário sem o", DOM, "convergiu no passo", fs5$prim$passo, "→ brms não acionado (D3)\n")

# ---------------------------------------------------------------- influência por centro (LOCO)
loco <- rbindlist(lapply(levels(e$centro), function(cc) {
  x <- e[centro != cc]; x[, centro := droplevels(centro)]
  r <- .fit_g(F("primeiros5"), x, glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))
  if (is.null(r$m)) return(data.table(centro_excluido = cc, OR = NA_real_))
  or_tab(list(m = r$m), "primeiros5")[, .(centro_excluido = cc, AIH_excl = e[centro == cc, .N], obitos_excl = e[centro == cc, sum(morte)], OR, lo, hi, avisos = length(r$msgs))]
}))
cat("\n== LOCO (primário): OR de", round(min(loco$OR, na.rm = TRUE), 2), "a", round(max(loco$OR, na.rm = TRUE), 2), "\n")
print(loco[order(-abs(log(OR) - log(res[amostra == A_TODOS & termo == "5 primeiros", OR])))][1:5])

# ---------------------------------------------------------------- descrição por blocos e Figura 5
desc_bl <- rbind(e[, .(amostra = A_TODOS, AIH = .N, obitos = sum(morte)), by = bloco], e5[, .(amostra = A_SEM, AIH = .N, obitos = sum(morte)), by = bloco])
desc_bl[, mort_bruta := 100 * obitos / AIH]
fig_dat <- function(fs, dat, rot) {
  nd <- setNames(lapply(c("1-5", "6-10", "11-15", "16-20", ">20"), function(b) { x <- copy(dat); x[, bloco := factor(b, levels = levels(dat$bloco))]; x }),
                 c("1-5", "6-10", "11-15", "16-20", ">20"))
  r1 <- marg(fs$bloco, nd)[, tipo := "Blocos de 5 casos"]
  nd2 <- list(`1-5` = copy(dat)[, primeiros5 := 1L], `>5` = copy(dat)[, primeiros5 := 0L])
  r2 <- marg(fs$prim, nd2)[, tipo := "Indicador primário (5 primeiros × demais)"]
  r <- rbind(r1, r2)[, amostra := rot]
  n1 <- dat[, .(n = .N, ob = sum(morte)), by = .(ponto = as.character(bloco))]
  n2 <- dat[, .(n = .N, ob = sum(morte)), by = .(ponto = fifelse(primeiros5 == 1, "1-5", ">5"))]
  merge(r, rbind(n1[, tipo := "Blocos de 5 casos"], n2[, tipo := "Indicador primário (5 primeiros × demais)"]), by = c("ponto", "tipo"))
}
R_TODOS <- sprintf("Todos os %d centros (%d AIH, %d óbitos)", NE, nrow(e), sum(e$morte)); R_SEM <- sprintf("Sem o %s (%d AIH, %d óbitos)", DOM, nrow(e5), sum(e5$morte))
f5 <- rbind(fig_dat(fa, e, R_TODOS), fig_dat(fs5, e5, R_SEM))
f5[, ponto := factor(ponto, levels = c("1-5", "6-10", "11-15", "16-20", ">20", ">5"))]
f5[, amostra := factor(amostra, levels = c(R_TODOS, R_SEM))]
p5 <- ggplot(f5, aes(ponto, est, colour = tipo)) +
  geom_pointrange(aes(ymin = lo, ymax = hi), position = position_dodge(width = 0.6)) +
  geom_text(aes(y = hi, label = paste0(ob, "/", n)), position = position_dodge(width = 0.6), vjust = -0.5, size = 2.4, show.legend = FALSE) +
  facet_wrap(~ amostra) + scale_colour_manual(values = PAL[1:2], name = NULL) +
  labs(x = "Nº sequencial do caso no centro", y = "Óbito hospitalar ajustado, % (IC95%)",
       title = paste0("Mortalidade hospitalar ajustada pelo nº do caso nos centros com 1º transplante observado ≥", ENT),
       subtitle = "Exploratório. Ajuste: faixa etária, sexo, ano (spline); intercepto aleatório de centro. Rótulos = óbitos/AIH") + tema
ggsave(file.path(out, "Figura5_aprendizado.png"), p5, width = 10, height = 5, dpi = 200, bg = "white")

# ---------------------------------------------------------------- comparação contextual com os centros incumbentes
d[, grupo := factor(fifelse(!entrante, LAB_INC_H, fifelse(seq <= 5, "Entrante casos 1-5", fifelse(seq <= 20, "Entrante casos 6-20", "Entrante casos >20"))),
                    levels = c(LAB_INC_H, "Entrante casos 1-5", "Entrante casos 6-20", "Entrante casos >20"))]
cat("\n== Comparação contextual com", tolower(LAB_INC), "\n")
fg <- escada(morte ~ grupo + faixa5 + sexoF + a1 + a2 + (1 | centro), d, NULL, sub("Centros", "comparação", LAB_INC_H))
comp <- merge(or_tab(fg, grep("grupo", nomes_b(fg), value = TRUE))[, grupo := sub("grupo", "", termo)],
              d[, .(AIH = .N, obitos = sum(morte)), by = grupo], by = "grupo", all.y = TRUE)
print(comp)

# ---------------------------------------------------------------- VLAD
grandes <- tam[n >= 20, as.character(centro)]
cat("\nVLAD: centros entrantes com ≥20 casos:", length(grandes), "\n")
vl <- rbindlist(lapply(sort(grandes), function(cc) {
  x <- e[centro == cc][order(seq)]
  sims <- replicate(2000, cumsum(x$p_risco - rbinom(nrow(x), 1, x$p_risco)))
  data.table(centro = cc, seq = x$seq, vlad = cumsum(x$p_risco - x$morte),
             lo = apply(sims, 1, quantile, 0.025), hi = apply(sims, 1, quantile, 0.975))
}))
pv <- ggplot(vl, aes(seq, vlad)) + geom_ribbon(aes(ymin = lo, ymax = hi), fill = "grey85") + geom_hline(yintercept = 0, linewidth = 0.3) +
  geom_step(colour = PAL[1]) + facet_wrap(~ centro, scales = "free_x") +
  labs(x = "Nº sequencial do caso", y = "Óbitos esperados − observados (acumulado)",
       title = paste0("VLAD ajustado por risco (faixa etária, sexo, ano) — centros com 1º TxC ≥", ENT, " e ≥20 casos"),
       subtitle = "Faixa cinza = 95% das trajetórias simuladas sob o modelo de risco. Descritivo; não é medida de desempenho") + tema
ggsave(file.path(out, "FiguraS4_VLAD.png"), pv, width = 10, height = 6, dpi = 200, bg = "white")

# conferência: contagens por bloco para o Python
dir.create(file.path(dirname(out), "_local"), showWarnings = FALSE)   # nível da AIH: fora do controle de versão
fwrite(e[, .(id_aih, centro, seq, morte)], file.path(dirname(out), "_local", "conf_seq.csv"))
escadas <- rbindlist(lapply(c(fa, fs5), function(f) data.table(modelo = f$rotulo, passo = f$passo, log = paste(f$log, collapse = " || "))))
salva_xlsx(list(Resultados = res, brms = if (is.null(bayes)) data.table(nota = paste("não acionado: primário sem", DOM, "convergiu")) else bayes,
                LOCO = loco, Blocos_descricao = desc_bl, Figura5_dados = f5, Comparacao_incumbentes = comp, Escada = escadas),   # VLAD só em figura (trajetória caso a caso)
           file.path(out, "Bloco4_tabelas.xlsx"))
cat("\nArquivos:", paste(list.files(out), collapse = ", "), "\n")
sink()
