# Funções e preparo comuns aos modelos de óbito hospitalar (blocos 3–7).
suppressPackageStartupMessages({
  library(data.table); library(splines); library(lme4); library(Hmisc, include.only = "rcspline.eval")
  library(sandwich); library(lmtest); library(ggplot2); library(patchwork); library(openxlsx)
})
set.seed(20261013)
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "param.R"))
REG <- c("Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste")
fmt <- function(x, k = 2) formatC(x, format = "f", digits = k, big.mark = ".", decimal.mark = ",")
ic  <- function(e, lo, hi, k = 2) paste0(fmt(e, k), " (", fmt(lo, k), "–", fmt(hi, k), ")")
pfmt <- function(p) ifelse(is.na(p), "", ifelse(p < 0.001, "<0,001", fmt(p, 3)))

carrega <- function(base) {
  d <- fread(file.path(base, ARQ_AIH), colClasses = list(character = c("munic_res", "munic_hosp")))
  ca <- fread(file.path(base, "microdados/centro_ano.csv"))
  confere_base(d)
  d[, faixa5 := factor(fifelse(idade < 18, "<18", faixa_etaria), levels = c("18-39", "<18", "40-49", "50-59", "60+"))]
  d[, sexoF := factor(sexo, levels = c("M", "F"))]
  d[, ano := ano_inter]
  NSANO <<- ns(d$ano_inter, df = 2)                  # base fixa do ano (nós dos dados completos)
  d[, c("a1", "a2") := as.data.table(unclass(NSANO)[, 1:2])]
  d[, periodo := periodo(ano)]
  d[, V := volume_centro_ano]; d[, Vm1 := V - 1L]
  d[, entre := mean(Vm1), by = centro]; d[, dentro := Vm1 - entre]
  d[, dentro10 := dentro / 10]
  d[, Vcat := factor(cut(V, c(0, 9, 19, 39, Inf), labels = c("<10", "10-19", "20-39", ">=40")), levels = c("<10", "10-19", "20-39", ">=40"))]
  d[, entrante := tipo_centro == "entrante"]
  setorder(d, centro, ano_inter, mes_inter, id_aih)
  d[, seq_centro := seq_len(.N), by = centro]       # nº acumulado observado (todos os centros)
  d[(entrante), seq := seq_len(.N), by = centro]    # nº sequencial do caso nos centros novos
  d[, centro := factor(centro)]
  # modelo de risco (sem centro, sem volume)
  risco <- glm(morte ~ faixa5 + sexoF + a1 + a2, family = binomial, data = d)
  d[, p_risco := fitted(risco)]
  list(d = d, ca = ca, risco = risco)
}

# spline cúbica restrita com nós fixos (Harrell); devolve matriz n × 2
rcs2 <- function(x, knots) { b <- rcspline.eval(x, knots = knots, inclx = TRUE); colnames(b) <- c("l", "nl"); b }
ano_base <- function(dt) { b <- predict(NSANO, dt$ano_inter); dt[, c("a1", "a2") := as.data.table(unclass(b)[, 1:2])]; invisible(dt) }
add_rcs <- function(dt, var, knots, prefix) {
  b <- rcs2(dt[[var]], knots); dt[, (paste0(prefix, "1")) := b[, 1]]; dt[, (paste0(prefix, "2")) := b[, 2]]; invisible(dt)
}

# ------------------------------------------------------------------ escada de convergência
.conv_msgs <- function(m) { x <- m@optinfo$conv$lme4$messages; if (is.null(x)) character(0) else x }
.fit_g <- function(f, data, control = glmerControl()) {
  w <- character(0)
  m <- withCallingHandlers(tryCatch(do.call(glmer, list(formula = f, data = data, family = binomial, control = control)),
                                    error = function(e) { w <<- c(w, paste("ERRO:", conditionMessage(e))); NULL }),
                           warning = function(x) { w <<- c(w, conditionMessage(x)); invokeRestart("muffleWarning") })
  list(m = m, msgs = unique(c(w, if (!is.null(m)) .conv_msgs(m))))
}
.relgrad <- function(m) tryCatch(with(m@optinfo$derivs, max(abs(solve(Hessian, gradient)))), error = function(e) NA_real_)
# Diagnóstico do passo 2 (só registro; não altera nenhuma decisão): com DIAG_FILE definido, grava uma linha por ajuste
# (glmer padrão do passo 1, bobyqa do passo 2 e os 4 otimizadores) com logLik, distância ao maior logLik, gradiente
# relativo, mensagens do lme4 e maior diferença dos efeitos fixos em relação ao bobyqa (em EP do bobyqa).
.diag_reg <- function(rotulo, passo, r1, r2, fits) {
  arq <- Sys.getenv("DIAG_FILE"); if (arq == "" || is.null(r2$m)) return(invisible())
  todos <- c(list(`padrão (passo 1)` = r1$m, `bobyqa (passo 2)` = r2$m), fits)
  msgs <- c(list(r1$msgs, r2$msgs), lapply(fits, function(m) if (is.null(m)) "falhou" else .conv_msgs(m)))
  ll <- sapply(todos, function(m) if (is.null(m)) NA_real_ else as.numeric(logLik(m)))
  b0 <- fixef(r2$m); se0 <- sqrt(diag(as.matrix(vcov(r2$m))))
  dfx <- sapply(todos, function(m) if (is.null(m)) NA_real_ else max(abs(fixef(m)[names(b0)] - b0) / se0))
  out <- data.table(modelo = rotulo, passo = passo, ajuste = names(todos), logLik = ll, dif_logLik = ll - max(ll, na.rm = TRUE),
                    grad_rel = sapply(todos, function(m) if (is.null(m)) NA_real_ else .relgrad(m)),
                    dif_fixef_EP = dfx, mensagens = sapply(msgs, function(x) if (length(x)) paste(x, collapse = " | ") else "nenhuma"))
  fwrite(out, arq, append = file.exists(arq))
}
escada <- function(f, data, f_linear = NULL, rotulo = "", verbose = TRUE) {
  log <- character(0); say <- function(...) { s <- paste0(...); log <<- c(log, s); if (verbose) cat("   ", s, "\n") }
  tenta <- function(f, p1, p2) {
    r1 <- .fit_g(f, data)
    if (!is.null(r1$m) && length(r1$msgs) == 0) { say("Passo ", p1, " (glmer padrão): convergiu"); return(list(m = r1$m, passo = as.integer(substr(p1, 1, 1)))) }
    say("Passo ", p1, " (glmer padrão): ", paste(r1$msgs, collapse = " | "))
    r2 <- .fit_g(f, data, glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))
    if (is.null(r2$m)) { say("Passo ", p2, ": falhou: ", paste(r2$msgs, collapse = " | ")); return(NULL) }
    rg <- .relgrad(r2$m)
    # equivalente ao allFit: 4 otimizadores; entre os que chegam ao mesmo ótimo (logLik a ≤0,001 do máximo),
    # discordância dos efeitos fixos em unidades de EP; o ajuste bobyqa precisa estar nesse conjunto
    fits <- lapply(c("bobyqa", "Nelder_Mead", "nloptwrap", "nlminbwrap"), function(o) {
      ctl <- if (o == "bobyqa") glmerControl(optimizer = o, optCtrl = list(maxfun = 2e5)) else glmerControl(optimizer = o)
      .fit_g(f, data, ctl)$m })
    names(fits) <- c("bobyqa", "Nelder_Mead", "nloptwrap", "nlminbwrap"); fits_todos <- fits
    fits <- fits[!sapply(fits, is.null)]
    ll <- sapply(fits, function(m) as.numeric(logLik(m))); ll2 <- as.numeric(logLik(r2$m))
    ok <- fits[ll >= max(c(ll, ll2)) - 1e-3]
    agree <- NA
    if (length(ok) >= 2 && ll2 >= max(c(ll, ll2)) - 1e-3) {
      fes <- do.call(rbind, lapply(ok, fixef)); se <- sqrt(diag(as.matrix(vcov(r2$m))))
      agree <- max(sweep(abs(sweep(fes, 2, apply(fes, 2, median))), 2, se, "/"))
    }
    .diag_reg(rotulo, p2, r1, r2, fits_todos)
    say(sprintf("Passo %s (bobyqa + 4 otimizadores): mensagens = %s; gradiente relativo = %.2g; otimizadores no mesmo ótimo = %d de %d; discordância máx. = %.2g EP",
                p2, if (length(r2$msgs)) paste(r2$msgs, collapse = " | ") else "nenhuma", rg, length(ok), length(fits), agree))
    # passo 2 aceito: outro otimizador (bobyqa) sem mensagens e gradiente relativo < 0,001; a concordância entre otimizadores é só relatada
    aceita <- length(r2$msgs) == 0 && !is.na(rg) && rg < 1e-3
    if (aceita) { say("Passo ", p2, ": aceito"); return(list(m = r2$m, passo = as.integer(substr(p2, 1, 1)))) }
    NULL
  }
  r <- tenta(f, "1", "2")
  if (is.null(r)) {
    m3 <- .fit_g(f, data, glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))$m
    if (!is.null(m3)) say("Passo 3: singular = ", isSingular(m3), "; DP do centro = ", signif(sqrt(VarCorr(m3)$centro[1]), 3))
    sep <- .separacao(f, data); if (length(sep)) say("Passo 3: separação em ", paste(sep, collapse = "; ")) else say("Passo 3: sem separação")
    if (!is.null(f_linear)) { say("Passo 4: spline → termo linear"); r <- tenta(f_linear, "4a", "4b"); if (!is.null(r)) r$passo <- 4 }
  }
  if (is.null(r)) {
    fg <- lme4::nobars(f)
    if (length(.separacao(f, data))) {   # Firth só se houver separação em estratos esparsos
      say("Passo 5: separação → logística de Firth (logistf, IC por verossimilhança perfilada), sem efeito de centro")
      g <- logistf::logistf(fg, data = as.data.frame(data), pl = TRUE)
      r <- list(m = g, passo = 5, vc = vcov(g), firth = TRUE)
    } else {
      say("Passo 5: logística com EP agrupado por centro")
      g <- glm(fg, family = binomial, data = data)
      r <- list(m = g, passo = 5, vc = vcovCL(g, cluster = data$centro))
    }
  }
  if (inherits(r$m, "glmerMod")) say("Singular: ", isSingular(r$m))
  r$log <- log; r$rotulo <- rotulo; r
}

.separacao <- function(f, data) {   # níveis de covariáveis categóricas/indicadoras sem óbito ou só com óbito
  vs <- intersect(all.vars(lme4::nobars(f))[-1], names(data)); out <- character(0)
  for (v in vs) { x <- data[[v]]; if (is.factor(x) || (is.numeric(x) && all(x %in% c(0, 1)))) {
    t <- data[, .(n = .N, ob = sum(morte)), by = v]; z <- t[ob == 0 | ob == n]
    if (nrow(z)) out <- c(out, paste0(v, " = ", z[[v]], " (", z$ob, "/", z$n, ")")) } }
  out
}
# coeficientes em OR (Wald) de glmerMod ou glm(+vcovCL)
nomes_b <- function(fit) names(if (inherits(fit$m, "glmerMod")) fixef(fit$m) else coef(fit$m))
or_tab <- function(fit, termos = NULL) {
  m <- fit$m
  b <- if (inherits(m, "glmerMod")) fixef(m) else coef(m)
  V <- if (!is.null(fit$vc)) fit$vc else as.matrix(vcov(m))
  se <- sqrt(diag(V)); k <- if (is.null(termos)) names(b) else intersect(termos, names(b))
  if (isTRUE(fit$firth)) { ci <- confint(m); return(data.table(termo = k, OR = exp(b[k]), lo = exp(ci[k, 1]), hi = exp(ci[k, 2]), p = m$prob[k])) }
  data.table(termo = k, OR = exp(b[k]), lo = exp(b[k] - 1.96 * se[k]), hi = exp(b[k] + 1.96 * se[k]), p = 2 * pnorm(-abs(b[k] / se[k])))
}
# contraste linear (OR) de combinações de coeficientes: L = matriz de pesos nomeada
or_contraste <- function(fit, L, nomes) {
  m <- fit$m; b <- if (inherits(m, "glmerMod")) fixef(m) else coef(m)
  V <- if (!is.null(fit$vc)) fit$vc else as.matrix(vcov(m))
  L <- L[, intersect(colnames(L), names(b)), drop = FALSE]; L2 <- matrix(0, nrow(L), length(b), dimnames = list(NULL, names(b))); L2[, colnames(L)] <- L; L <- L2; est <- drop(L %*% b); se <- sqrt(diag(L %*% V %*% t(L)))
  data.table(contraste = nomes, OR = exp(est), lo = exp(est - 1.96 * se), hi = exp(est + 1.96 * se), p = 2 * pnorm(-abs(est / se)))
}
icc_mor <- function(m) {
  s2 <- VarCorr(m)$centro[1]
  pr <- tryCatch(suppressWarnings(suppressMessages(confint(m, parm = "theta_", method = "profile", oldNames = FALSE))), error = function(e) NULL)
  sd_ci <- if (!is.null(pr)) as.numeric(pr[1, ]) else c(NA, NA)
  f <- function(s) c(ICC = s^2 / (s^2 + pi^2 / 3), MOR = exp(0.6745 * sqrt(2) * s))
  data.table(medida = c("DP do centro (logit)", "ICC (escala latente)", "OR mediano do centro"),
             est = c(sqrt(s2), f(sqrt(s2))), lo = c(sd_ci[1], f(sd_ci[1])), hi = c(sd_ci[2], f(sd_ci[2])))
}
# padronização marginal: média das prob. preditas (efeito aleatório = 0) com X substituído; IC por simulação
marg <- function(fit, newdata_list, nsim = 2000) {
  m <- fit$m; b <- if (inherits(m, "glmerMod")) fixef(m) else coef(m)
  V <- if (!is.null(fit$vc)) fit$vc else as.matrix(vcov(m))
  tt <- if (inherits(m, "glmerMod")) delete.response(terms(m, fixed.only = TRUE)) else delete.response(terms(m))  # mantém predvars (nós do ns)
  B <- MASS::mvrnorm(nsim, b, V)
  rbindlist(lapply(names(newdata_list), function(nm) {
    X <- model.matrix(tt, newdata_list[[nm]], xlev = if (inherits(m, "glmerMod")) NULL else m$xlevels)
    X <- X[, names(b), drop = FALSE]
    est <- mean(plogis(X %*% b)); sims <- colMeans(plogis(X %*% t(B)))
    data.table(ponto = nm, est = 100 * est, lo = 100 * quantile(sims, 0.025), hi = 100 * quantile(sims, 0.975))
  }))
}
salva_xlsx <- function(lista, arq) {
  wb <- createWorkbook()
  for (s in names(lista)) { addWorksheet(wb, substr(s, 1, 31)); writeData(wb, substr(s, 1, 31), lista[[s]]) }
  saveWorkbook(wb, arq, overwrite = TRUE)
}
# Paleta categórica de ordem fixa, distinguível com deficiência de visão de cores (ΔE adjacente ≥ 9,1);
# como 3 cores têm contraste < 3:1, rótulos e tabelas acompanham as figuras
PAL <- c("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
CORES_REG <- c(Brasil = "#0b0b0b", Norte = PAL[1], Nordeste = PAL[2], Sudeste = PAL[3], Sul = PAL[4], `Centro-Oeste` = PAL[5])
tema <- theme_minimal(base_size = 10) + theme(panel.grid.minor = element_blank(), legend.position = "bottom")
