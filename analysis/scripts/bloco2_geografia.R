# Bloco 2 — Utilização por região de residência: taxas padronizadas por idade e sexo, tendência, proximidade e distância
# Uso: LANG=C.UTF-8 Rscript scripts/bloco2_geografia.R data_2000_w04 outputs_2000_2025/bloco2

suppressPackageStartupMessages({
  library(data.table); library(splines); library(MASS); library(glmmTMB)
  library(geosphere); library(logistf); library(ggplot2); library(patchwork); library(openxlsx)
})
set.seed(20261013)
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "param.R"))
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"
out  <- if (length(args) >= 2) args[2] else "outputs/bloco2"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco2.txt"), split = TRUE)
cat("Bloco 2 —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n\n")

REG <- c("Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste")
FX6 <- c("0-11", "12-17", "18-39", "40-49", "50-59", "60+")
fmt <- function(x, k = 1) formatC(x, format = "f", digits = k, big.mark = ".", decimal.mark = ",")
ic  <- function(e, lo, hi, k = 1) paste0(fmt(e, k), " (", fmt(lo, k), "–", fmt(hi, k), ")")

# ---------------------------------------------------------------- dados
d  <- fread(file.path(base, ARQ_AIH),
            colClasses = list(character = c("munic_res", "munic_hosp")))
ca <- fread(file.path(base, "microdados/centro_ano.csv"))
pop <- fread(file.path(base, "ibge_covariaveis/pop_uf_ano_sexo_idade.csv"))[tipo_faixa == "analise"]
coord <- fread(file.path(base, "ibge_covariaveis/municipios_coord.csv"),
               colClasses = list(character = c("codigo7", "codigo")))
cz <- read.xlsx(file.path(base, "ibge_covariaveis/CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF.xlsx"),
                sheet = 1, startRow = 3)
cz <- as.data.table(cz)[, .(uf = cz[[1]], codigo7 = paste0(sprintf("%02d", as.integer(cz[[2]])), cz[[3]]), pop22 = cz[[7]])]
cz <- cz[!is.na(pop22) & nchar(codigo7) == 7]

d[, periodo := periodo(ano_inter)]
d[, faixa_etaria := factor(faixa_etaria, levels = FX6)]
d[, faixa5 := factor(fifelse(idade < 18, "<18", as.character(faixa_etaria)),
                     levels = c("18-39", "<18", "40-49", "50-59", "60+"))]
d[, regiao_res := factor(regiao_res, levels = REG)]
d[, ped := as.integer(idade < 18)]
confere_base(d); stopifnot(all(d$ped == d$pediatrico))
d_all <- copy(d)   # todas as AIH (centros ativos por ano não dependem da residência)
d[uf_res == "", uf_res := NA_character_]
if (anyNA(d$uf_res)) {   # MUNIC_RES "000000" (residência ignorada) em 15 AIH de 2005–2006
  cat("AIH sem município de residência (excluídas deste bloco, que é por residência):", sum(is.na(d$uf_res)), "\n"); print(d[is.na(uf_res), .N, by = ano_inter])
  d <- d[!is.na(uf_res)]
}
uf_reg <- unique(pop[, .(uf, regiao)])
cat("AIH:", nrow(d), "| residentes por região:\n"); print(d[, .N, by = regiao_res][order(regiao_res)])

# ---------------------------------------------------------------- taxa padronizada (Fay–Feuer)
pad <- pop[ano == 2025, .(p = sum(populacao)), by = .(faixa_etaria, sexo)][, w := p / sum(p)]
dsr <- function(x, n, w) {
  r <- sum(w * x / n); v <- sum(w^2 * x / n^2); wm <- max(w / n)
  lo <- if (sum(x) == 0) 0 else v / (2 * r) * qchisq(0.025, 2 * r^2 / v)
  hi <- (v + wm^2) / (2 * (r + wm)) * qchisq(0.975, 2 * (r + wm)^2 / (v + wm^2))
  list(dsr = r * 1e6, lo = lo * 1e6, hi = hi * 1e6, var = v * 1e12)
}
pois_ic <- function(x, py) list(bruta = x / py * 1e6,
  lo = if (x == 0) 0 else qchisq(0.025, 2 * x) / 2 / py * 1e6, hi = qchisq(0.975, 2 * x + 2) / 2 / py * 1e6)

pop[, periodo := periodo(ano)]
strata <- CJ(faixa_etaria = FX6, sexo = c("F", "M"))
taxa_grupo <- function(dd, pp, by_sex_std = FALSE) {
  x  <- dd[, .(x = .N), by = .(faixa_etaria, sexo)]
  py <- pp[, .(py = sum(populacao)), by = .(faixa_etaria, sexo)]
  s  <- merge(merge(strata, py, by = c("faixa_etaria", "sexo"), all.x = TRUE), x, by = c("faixa_etaria", "sexo"), all.x = TRUE)
  s[is.na(x), x := 0L]; s <- merge(s, pad[, .(faixa_etaria, sexo, w)], by = c("faixa_etaria", "sexo"))
  r <- dsr(s$x, s$py, s$w); b <- pois_ic(sum(s$x), sum(s$py))
  data.table(n = sum(s$x), py = sum(s$py), bruta = b$bruta, bruta_lo = b$lo, bruta_hi = b$hi,
             dsr = r$dsr, dsr_lo = r$lo, dsr_hi = r$hi, dsr_var = r$var)
}
geo_grid <- rbind(data.table(nivel = "Brasil", local = "Brasil"),
                  data.table(nivel = "Região", local = REG))
tx_reg <- rbindlist(lapply(seq_len(nrow(geo_grid)), function(i) {
  g <- geo_grid[i]; rbindlist(lapply(c(PER, PER_TOT), function(pe) {
    dd <- d[if (g$nivel == "Brasil") TRUE else regiao_res == g$local][if (pe == PER_TOT) TRUE else periodo == pe]
    pp <- pop[if (g$nivel == "Brasil") TRUE else regiao == g$local][if (pe == PER_TOT) TRUE else periodo == pe]
    cbind(g, periodo = pe, taxa_grupo(dd, pp))
  }))
}))
cat("\n== Taxa anual de TxC por milhão, por região de residência e período\n")
print(tx_reg[, .(local, periodo, n, bruta = round(bruta, 2), dsr = round(dsr, 2), lo = round(dsr_lo, 2), hi = round(dsr_hi, 2))])

tx_uf <- rbindlist(lapply(sort(unique(pop$uf)), function(u) rbindlist(lapply(c(PER, PER_TOT), function(pe) {
  dd <- d[uf_res == u][if (pe == PER_TOT) TRUE else periodo == pe]
  pp <- pop[uf == u][if (pe == PER_TOT) TRUE else periodo == pe]
  r <- cbind(data.table(uf = u, regiao = uf_reg[uf == u, regiao], periodo = pe), taxa_grupo(dd, pp))
  if (r$n < 10) r[, c("dsr", "dsr_lo", "dsr_hi") := NA_real_]   # taxa não estimada com <10 casos
  r
}))))

# ---------------------------------------------------------------- tendência região × ano
ry <- CJ(regiao = REG, ano = ANOS)
ry <- merge(ry, d[, .(n = .N), by = .(regiao = as.character(regiao_res), ano = ano_inter)], all.x = TRUE)[is.na(n), n := 0L]
ry <- merge(ry, pop[, .(pop = sum(populacao)), by = .(regiao, ano)], by = c("regiao", "ano"))
ncr <- ca[n_txc >= 1, .(ncent = .N), by = .(regiao = regiao_hosp, ano)]
ry <- merge(ry, ncr, by = c("regiao", "ano"), all.x = TRUE)[is.na(ncent), ncent := 0L]
ry[, regiao := relevel(factor(regiao, levels = REG), ref = "Sudeste")]

qres <- function(y, mu, theta = NULL) {   # resíduos quantílicos aleatorizados (Dunn–Smyth)
  if (is.null(theta)) { a <- ppois(y - 1, mu); b <- ppois(y, mu) } else {
    a <- pnbinom(y - 1, size = theta, mu = mu); b <- pnbinom(y, size = theta, mu = mu) }
  qnorm(runif(length(y), a, b))
}
disp_test <- function(mP, mNB) {
  lr <- as.numeric(2 * (logLik(mNB) - logLik(mP)))
  list(pearson_gl = sum(residuals(mP, "pearson")^2) / df.residual(mP), lrt = lr,
       p = 0.5 * pchisq(max(lr, 0), 1, lower.tail = FALSE))
}
f1 <- n ~ ns(ano, df = 2) + regiao + offset(log(pop))
mP  <- glm(f1, family = poisson, data = ry)
mNB <- glm.nb(f1, data = ry)
dt1 <- disp_test(mP, mNB)
usa_nb <- dt1$p < 0.05
cat(sprintf("\n== Região × ano: Pearson/gl (Poisson) = %.2f; LRT Poisson × BN = %.2f, p = %.3g → %s\n",
            dt1$pearson_gl, dt1$lrt, dt1$p, if (usa_nb) "binomial negativa" else "Poisson"))
fit_cnt <- function(f) if (usa_nb) glm.nb(f, data = ry) else glm(f, family = poisson, data = ry)
m1 <- fit_cnt(f1)
m2 <- fit_cnt(update(f1, . ~ . + ncent))
m0 <- fit_cnt(n ~ regiao + offset(log(pop)))
mL <- fit_cnt(n ~ ano + regiao + offset(log(pop)))
th <- if (usa_nb) m1$theta else NULL
qr1 <- qres(ry$n, fitted(m1), th)
ks1 <- ks.test(qr1, "pnorm")
cat("Convergiu:", m1$converged, "| theta:", if (usa_nb) round(m1$theta, 2) else NA,
    "| KS resíduos quantílicos p =", signif(ks1$p.value, 3), "\n")
lrt <- function(a, b) { s <- as.numeric(2 * (logLik(b) - logLik(a))); k <- attr(logLik(b), "df") - attr(logLik(a), "df")
  c(LR = s, gl = k, p = pchisq(s, k, lower.tail = FALSE)) }
cat("Ano (spline 2 gl) vs sem ano:"); print(round(lrt(m0, m1), 4))
cat("Spline vs ano linear (não linearidade):"); print(round(lrt(mL, m1), 4))
irr_tab <- function(m, lab) {
  b <- coef(m); se <- sqrt(diag(vcov(m))); k <- !grepl("ns\\(|Intercept", names(b))
  data.table(modelo = lab, termo = names(b)[k], IRR = exp(b[k]), lo = exp(b[k] - 1.96 * se[k]), hi = exp(b[k] + 1.96 * se[k]),
             p = 2 * pnorm(-abs(b[k] / se[k])))
}
tend <- rbind(irr_tab(m1, "M1: ns(ano,2) + região"), irr_tab(m2, "M2: M1 + nº centros ativos na região (descritivo)"))
print(tend[, .(modelo, termo, IRR = round(IRR, 3), lo = round(lo, 3), hi = round(hi, 3), p = signif(p, 3))])
nd <- copy(ry)[, pop := 1e6]
pr <- predict(m1, newdata = nd, type = "link", se.fit = TRUE)
ry[, `:=`(pred = exp(pr$fit), pred_lo = exp(pr$fit - 1.96 * pr$se.fit), pred_hi = exp(pr$fit + 1.96 * pr$se.fit))]

# ---------------------------------------------------------------- UF × ano (parcimonioso)
uy <- CJ(uf = sort(unique(pop$uf)), ano = ANOS)
uy <- merge(uy, d[, .(n = .N), by = .(uf = uf_res, ano = ano_inter)], all.x = TRUE)[is.na(n), n := 0L]
uy <- merge(uy, pop[, .(pop = sum(populacao)), by = .(uf, ano)], by = c("uf", "ano"))
ncu <- ca[n_txc >= 1, .(ncent = .N), by = .(uf = uf_hosp, ano)]
uy <- merge(uy, ncu, by = c("uf", "ano"), all.x = TRUE)[is.na(ncent), ncent := 0L]
cat(sprintf("\n== UF × ano: %d células, %d com zero; UFs sem nenhum caso: %s\n", nrow(uy), sum(uy$n == 0),
            paste(uy[, sum(n), by = uf][V1 == 0, uf], collapse = ", ")))
f_uf <- n ~ ns(ano, df = 2) + (1 | uf) + offset(log(pop))
ok_fit <- function(m) !is.null(m) && m$fit$convergence == 0 && isTRUE(m$sdr$pdHess) && all(is.finite(sqrt(diag(vcov(m)$cond))))
gtry <- function(expr) tryCatch(expr, error = function(e) { cat("ERRO:", conditionMessage(e), "\n"); NULL },
                                warning = function(w) { cat("AVISO:", conditionMessage(w), "\n"); NULL })
uP  <- gtry(glmmTMB(f_uf, family = poisson, data = uy))
uNB <- gtry(glmmTMB(f_uf, family = nbinom2, data = uy))
uf_res_mod <- NULL
if (ok_fit(uP) && ok_fit(uNB)) {
  lr <- as.numeric(2 * (logLik(uNB) - logLik(uP))); pu <- 0.5 * pchisq(max(lr, 0), 1, lower.tail = FALSE)
  pear <- sum(residuals(uP, "pearson")^2) / df.residual(uP)
  um <- if (pu < 0.05) uNB else uP
  cat(sprintf("Pearson/gl (Poisson) = %.2f; LRT Poisson × BN = %.2f, p = %.3g → %s\n", pear, lr, pu, if (pu < 0.05) "nbinom2" else "Poisson"))
  um2 <- gtry(glmmTMB(update(f_uf, . ~ . + ncent), family = family(um)$family, data = uy))
  qru <- qres(uy$n, fitted(um), if (pu < 0.05) sigma(um) else NULL)
  cat("KS resíduos quantílicos p =", signif(ks.test(qru, "pnorm")$p.value, 3),
      "| DP do intercepto aleatório de UF =", round(sqrt(VarCorr(um)$cond$uf[1]), 3), "\n")
  if (ok_fit(um) && ok_fit(um2)) {
    b <- fixef(um2)$cond; se <- sqrt(diag(vcov(um2)$cond))
    uf_res_mod <- data.table(modelo = c("UF: ns(ano,2) + (1|UF)", "UF: + nº centros ativos na UF (descritivo)"),
      dp_uf = c(sqrt(VarCorr(um)$cond$uf[1]), sqrt(VarCorr(um2)$cond$uf[1])),
      IRR_ncent = c(NA, exp(b["ncent"])), lo = c(NA, exp(b["ncent"] - 1.96 * se["ncent"])), hi = c(NA, exp(b["ncent"] + 1.96 * se["ncent"])),
      familia = family(um)$family, KS_p = ks.test(qru, "pnorm")$p.value)
    print(uf_res_mod)
  }
}
if (is.null(uf_res_mod)) cat("Modelo UF × ano não atendeu aos critérios (B5): utilização por UF fica só descritiva.\n")

# ---------------------------------------------------------------- proximidade geográfica potencial
coord[, cod6 := codigo]
mun <- merge(cz, coord[, .(codigo7, cod6, lat, lon)], by = "codigo7", all = TRUE)
cat(sprintf("\n== Municípios: Censo %d, coordenadas %d, pareados %d; sem coordenada: %d; sem população: %d\n",
            nrow(cz), nrow(coord), mun[!is.na(pop22) & !is.na(lat), .N], mun[is.na(lat), .N], mun[is.na(pop22), .N]))
print(mun[is.na(pop22) | is.na(lat)])
mun <- mun[!is.na(pop22) & !is.na(lat)]
mun <- merge(mun, uf_reg, by = "uf")
cat("População coberta:", fmt(sum(mun$pop22), 0), "\n")
d[, munic_hosp_geo := fifelse(substr(munic_hosp, 1, 2) == "53", "530010", munic_hosp)]
d[, munic_res_geo  := fifelse(substr(munic_res, 1, 2) == "53", "530010", munic_res)]
cy <- d_all[, .(n = .N), by = .(centro, ano = ano_inter, cod6 = fifelse(substr(munic_hosp, 1, 2) == "53", "530010", munic_hosp), uf_c = uf_hosp)]
stopifnot(all.equal(cy[, sum(n), by = .(centro, ano)][order(centro, ano)]$V1,
                    ca[n_txc > 0][order(centro, ano)]$n_txc))
cy <- merge(cy, coord[, .(cod6, lat, lon)], by = "cod6")
XY <- as.matrix(mun[, .(lon, lat)])
prox <- rbindlist(lapply(ANOS, function(a) rbindlist(lapply(c(1, 5), function(lim) {
  cc <- unique(cy[ano == a & n >= lim, .(cod6, uf_c, lon, lat)])
  D <- distm(XY, as.matrix(cc[, .(lon, lat)]), fun = distGeo) / 1000
  dmin <- apply(D, 1, min)
  Duf <- D; Duf[outer(mun$uf, cc$uf_c, "!=")] <- Inf
  data.table(ano = a, limiar = lim, cod6 = mun$cod6, uf = mun$uf, regiao = mun$regiao, pop22 = mun$pop22,
             dmin = dmin, dmin_uf = apply(Duf, 1, min), n_mun_centro = nrow(cc))
}))))
# conferência por segundo caminho: distância ao centro mais próximo recalculada × variável do banco
chk <- merge(d[, .(ano = ano_inter, cod6 = munic_res_geo, dist_banco = dist_km_centro_mais_proximo_ano)],
             prox[limiar == 1, .(ano, cod6, dmin)], by = c("ano", "cod6"))
cat(sprintf("Conferência dist. ao centro mais próximo (n = %d AIH): |diferença| máx = %.2f km; >1 km: %d\n",
            nrow(chk), max(abs(chk$dist_banco - chk$dmin)), sum(abs(chk$dist_banco - chk$dmin) > 1)))
chk2 <- merge(d[, .(cod6 = munic_res_geo, h = munic_hosp_geo, dist_banco = dist_km_centro_operou)],
              coord[, .(cod6, la1 = lat, lo1 = lon)], by = "cod6")
chk2 <- merge(chk2, coord[, .(h = cod6, la2 = lat, lo2 = lon)], by = "h")
chk2[, dk := distGeo(cbind(lo1, la1), cbind(lo2, la2)) / 1000]
cat(sprintf("Conferência distância percorrida: |diferença| máx = %.2f km\n", max(abs(chk2$dist_banco - chk2$dk))))

prox_sum <- function(by) prox[, .(
  le300 = 100 * sum(pop22[dmin <= 300]) / sum(pop22), le500 = 100 * sum(pop22[dmin <= 500]) / sum(pop22),
  le1000 = 100 * sum(pop22[dmin <= 1000]) / sum(pop22), le500_mesma_uf = 100 * sum(pop22[dmin_uf <= 500]) / sum(pop22),
  municipios_com_centro = n_mun_centro[1]), by = by]
prox_ano <- rbind(prox_sum(c("ano", "limiar"))[, local := "Brasil"], setnames(prox_sum(c("ano", "limiar", "regiao")), "regiao", "local"), use.names = TRUE)
prox_ano[, periodo := as.character(periodo(ano))]
prox_per <- prox_ano[, lapply(.SD, mean), by = .(local, periodo, limiar), .SDcols = c("le300", "le500", "le1000", "le500_mesma_uf")]
cat("\n== Proximidade (% da população a ≤ X km de centro ativo), Brasil, por ano\n")
print(dcast(prox_ano[local == "Brasil"], ano ~ limiar, value.var = c("le300", "le500", "le1000"))[, lapply(.SD, round, 1)])

# ---------------------------------------------------------------- distância percorrida e fora da UF
q75 <- function(x) as.numeric(quantile(x, 0.75, type = 7))
dist_ano <- rbind(d[, .(local = "Brasil", n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou),
                        fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf)), by = .(ano = ano_inter)],
                  d[, .(n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou),
                        fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf)), by = .(local = as.character(regiao_res), ano = ano_inter)])
dist_per <- rbind(d[, .(local = "Brasil", n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou),
                        fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf)), by = .(periodo = as.character(periodo))],
                  d[, .(n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou),
                        fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf)), by = .(local = as.character(regiao_res), periodo = as.character(periodo))])
dist_per <- rbind(dist_per,
  d[, .(local = "Brasil", periodo = PER_TOT, n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou), fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf))],
  d[, .(periodo = PER_TOT, n = .N, mediana = median(dist_km_centro_operou), P75 = q75(dist_km_centro_operou), fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf)), by = .(local = as.character(regiao_res))])
cat("\n== Distância percorrida (km) e fora da UF, Brasil, por ano\n"); print(dist_ano[local == "Brasil"][order(ano)])

d[, dcat := cut(dist_km_centro_mais_proximo_ano, c(-Inf, 0, 100, 300, 500, Inf),
                labels = c("0 km", ">0-100", ">100-300", ">300-500", ">500"))]
d[, sexoF := factor(sexo, levels = c("M", "F"))]
d[, reg_ref := relevel(regiao_res, ref = "Sudeste")]
cat("\nFora da UF por região de residência e categoria de distância (n fora / N):\n")
print(dcast(d[, .(v = paste0(sum(fora_uf), "/", .N)), by = .(reg_ref, dcat)], reg_ref ~ dcat, value.var = "v"))
mf <- logistf(fora_uf ~ faixa5 + sexoF + reg_ref + ns(ano_inter, df = 2) + dcat, data = as.data.frame(d), pl = TRUE)
fora_mod <- data.table(termo = names(coef(mf)), OR = exp(coef(mf)), lo = exp(mf$ci.lower), hi = exp(mf$ci.upper), p = mf$prob)[!grepl("Intercept|ns\\(", termo)]
cat("\n== Fora da UF, logística de Firth (descritiva)\n"); print(fora_mod[, .(termo, OR = signif(OR, 3), lo = signif(lo, 3), hi = signif(hi, 3), p = signif(p, 3))])

# ---------------------------------------------------------------- MS, SE, MA (três casos, só descrição)
casos3 <- rbindlist(lapply(c("MS", "SE", "MA"), function(u) {
  g <- CJ(ano = ANOS)
  r <- d[uf_res == u, .(residentes = .N, na_propria_uf = sum(fora_uf == 0), fora_uf = sum(fora_uf),
                       dist_mediana = median(dist_km_centro_operou)), by = .(ano = ano_inter)]
  h <- d[uf_hosp == u, .(AIH_em_centro_da_uf = .N), by = .(ano = ano_inter)]
  x <- merge(merge(g, r, all.x = TRUE), h, all.x = TRUE)
  for (v in c("residentes", "na_propria_uf", "fora_uf", "AIH_em_centro_da_uf")) set(x, which(is.na(x[[v]])), v, 0L)
  cbind(uf = u, primeiro_centro = ca[uf_hosp == u & n_txc > 0, min(ano)], x)
}))
cat("\n== MS, SE, MA (descrição)\n"); print(casos3[residentes > 0 | AIH_em_centro_da_uf > 0])

# ---------------------------------------------------------------- crianças
popk <- pop[faixa_etaria %in% c("0-11", "12-17")]
kid_tx <- rbindlist(lapply(seq_len(nrow(geo_grid)), function(i) {
  g <- geo_grid[i]; rbindlist(lapply(c(PER, PER_TOT), function(pe) {
    x  <- d[ped == 1][if (g$nivel == "Brasil") TRUE else regiao_res == g$local][if (pe == PER_TOT) TRUE else periodo == pe, .N]
    py <- popk[if (g$nivel == "Brasil") TRUE else regiao == g$local][if (pe == PER_TOT) TRUE else periodo == pe, sum(populacao)]
    b <- pois_ic(x, py); cbind(g, periodo = pe, n = x, taxa = b$bruta, lo = b$lo, hi = b$hi)
  }))
}))
kid_vs_ad <- d[, .(n = .N, fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf), dist_mediana = median(dist_km_centro_operou),
                   dist_P75 = q75(dist_km_centro_operou)), by = .(grupo = fifelse(ped == 1, "Crianças (<18)", "Adultos"), periodo = as.character(periodo))]
kid_vs_ad <- rbind(kid_vs_ad, d[, .(periodo = PER_TOT, n = .N, fora_n = sum(fora_uf), fora_pct = 100 * mean(fora_uf),
                   dist_mediana = median(dist_km_centro_operou), dist_P75 = q75(dist_km_centro_operou)),
                   by = .(grupo = fifelse(ped == 1, "Crianças (<18)", "Adultos"))])
ped_cent <- dcast(ca[n_ped >= 1, .N, by = .(ano, regiao_hosp)], ano ~ regiao_hosp, value.var = "N", fill = 0)
ped_cent[, Total := rowSums(.SD), .SDcols = -"ano"]
cat("\n== Crianças: taxa por milhão de residentes 0–17\n"); print(kid_tx[, .(local, periodo, n, taxa = round(taxa, 2), lo = round(lo, 2), hi = round(hi, 2))])
cat("\nCrianças × adultos\n"); print(kid_vs_ad[order(periodo, grupo)])
cat("\nCentros com ≥1 TxC pediátrico por ano e região do hospital\n"); print(ped_cent)

# ---------------------------------------------------------------- mulheres
pad_age <- pop[ano == 2025, .(p = sum(populacao)), by = faixa_etaria][, w := p / sum(p)]
taxa_sexo <- function(dd, pp, sx) {
  x  <- dd[sexo == sx, .(x = .N), by = faixa_etaria]
  py <- pp[sexo == sx, .(py = sum(populacao)), by = faixa_etaria]
  s <- merge(merge(pad_age[, .(faixa_etaria, w)], py, by = "faixa_etaria"), x, by = "faixa_etaria", all.x = TRUE)
  s[is.na(x), x := 0L]; r <- dsr(s$x, s$py, s$w); c(n = sum(s$x), r)
}
mulh <- rbindlist(lapply(seq_len(nrow(geo_grid)), function(i) {
  g <- geo_grid[i]; rbindlist(lapply(c(PER, PER_TOT), function(pe) {
    dd <- d[if (g$nivel == "Brasil") TRUE else regiao_res == g$local][if (pe == PER_TOT) TRUE else periodo == pe]
    pp <- pop[if (g$nivel == "Brasil") TRUE else regiao == g$local][if (pe == PER_TOT) TRUE else periodo == pe]
    f <- taxa_sexo(dd, pp, "F"); m <- taxa_sexo(dd, pp, "M")
    rr <- f$dsr / m$dsr; se <- sqrt(f$var / f$dsr^2 + m$var / m$dsr^2)
    cbind(g, periodo = pe, n_F = f$n, dsr_F = f$dsr, F_lo = f$lo, F_hi = f$hi, n_M = m$n, dsr_M = m$dsr, M_lo = m$lo, M_hi = m$hi,
          razao_FM = rr, razao_lo = if (f$n > 0) rr * exp(-1.96 * se) else NA, razao_hi = if (f$n > 0) rr * exp(1.96 * se) else NA)
  }))
}))
cat("\n== Mulheres: taxa padronizada por idade por sexo e razão M/H\n")
print(mulh[, .(local, periodo, n_F, n_M, dsr_F = round(dsr_F, 2), dsr_M = round(dsr_M, 2), razao = round(razao_FM, 2), lo = round(razao_lo, 2), hi = round(razao_hi, 2))])
d[, fem := as.integer(sexo == "F")]
gF  <- glm(fem ~ I((ano_inter - INI) / 5), family = binomial, data = d)
gF2 <- glm(fem ~ ns(ano_inter, df = 2), family = binomial, data = d)
bF <- coef(gF)[2]; seF <- sqrt(vcov(gF)[2, 2])
mulh_tend <- data.table(OR_por_5_anos = exp(bF), lo = exp(bF - 1.96 * seF), hi = exp(bF + 1.96 * seF), p = 2 * pnorm(-abs(bF / seF)),
                        p_nao_linear = anova(gF, gF2, test = "LRT")$`Pr(>Chi)`[2])
mulh_ano <- d[, .(n = .N, mulheres = sum(fem), pct = 100 * mean(fem)), by = .(ano = ano_inter)][order(ano)]
cat("Proporção de mulheres: OR por 5 anos\n"); print(mulh_tend); print(mulh_ano)

# ---------------------------------------------------------------- Tabela 3
pw <- function(x) fmt(x, 1)
t3 <- merge(tx_reg[, .(local, periodo, n, bruta, dsr, dsr_lo, dsr_hi)], dist_per, by = c("local", "periodo", "n"), all.x = TRUE)
pp1 <- prox_per[limiar == 1, .(local, periodo, p1_300 = le300, p1_500 = le500, p1_1000 = le1000)]
pp5 <- prox_per[limiar == 5, .(local, periodo, p5_300 = le300, p5_500 = le500, p5_1000 = le1000)]
t3 <- merge(merge(t3, pp1, by = c("local", "periodo"), all.x = TRUE), pp5, by = c("local", "periodo"), all.x = TRUE)
t3[, ordem := match(local, c("Brasil", REG))][, op := match(periodo, c(PER, PER_TOT))]
setorder(t3, ordem, op)
Tabela3 <- t3[, .(`Região de residência` = local, `Período` = periodo, `TxC, n` = n,
  `Taxa bruta/milhão/ano` = fmt(bruta, 2), `Taxa padronizada/milhão/ano (IC95%)` = ic(dsr, dsr_lo, dsr_hi, 2),
  `Distância percorrida, km, mediana (P75)` = paste0(fmt(mediana, 0), " (", fmt(P75, 0), ")"),
  `Fora da UF, n (%)` = paste0(fora_n, " (", fmt(fora_pct, 1), ")"),
  `≤300 km, % pop. (centro ≥1 | ≥5)` = paste0(pw(p1_300), " | ", pw(p5_300)),
  `≤500 km, % pop. (centro ≥1 | ≥5)` = paste0(pw(p1_500), " | ", pw(p5_500)),
  `≤1.000 km, % pop. (centro ≥1 | ≥5)` = paste0(pw(p1_1000), " | ", pw(p5_1000)))]
Tabela3[`Período` == PER_TOT, grep("km, % pop", names(Tabela3), value = TRUE) := "—"]

# ---------------------------------------------------------------- Tabela 5
k <- merge(kid_vs_ad[grupo != "Adultos"], kid_vs_ad[grupo == "Adultos"], by = "periodo", suffixes = c("_c", "_a"))
kb <- kid_tx[local == "Brasil", .(periodo, taxa_c = ic(taxa, lo, hi, 2))]
pc <- ca[n_ped >= 1, .N, by = ano][, periodo := as.character(periodo(ano))][, .(cent_ped = paste0(min(N), "–", max(N))), by = periodo]
pc <- rbind(pc, data.table(periodo = PER_TOT, cent_ped = paste0(ca[n_ped >= 1, .N, by = ano][, paste0(min(N), "–", max(N))])))
mb <- mulh[local == "Brasil", .(periodo, txF = ic(dsr_F, F_lo, F_hi, 2), txM = ic(dsr_M, M_lo, M_hi, 2),
                                razao = ic(razao_FM, razao_lo, razao_hi, 2), nF = n_F, nM = n_M)]
t5 <- Reduce(function(a, b) merge(a, b, by = "periodo"), list(k, kb, pc, mb))
t5[, op := match(periodo, c(PER, PER_TOT))]; setorder(t5, op)
Tabela5 <- t5[, .(`Período` = periodo,
  `Crianças, n` = n_c, `Taxa crianças/milhão 0–17 anos/ano (IC95%)` = taxa_c,
  `Fora da UF, crianças n (%)` = paste0(fora_n_c, " (", fmt(fora_pct_c), ")"), `Fora da UF, adultos n (%)` = paste0(fora_n_a, " (", fmt(fora_pct_a), ")"),
  `Distância, crianças, km, mediana (P75)` = paste0(fmt(dist_mediana_c, 0), " (", fmt(dist_P75_c, 0), ")"),
  `Distância, adultos, km, mediana (P75)` = paste0(fmt(dist_mediana_a, 0), " (", fmt(dist_P75_a, 0), ")"),
  `Centros com ≥1 TxC pediátrico/ano (mín–máx)` = cent_ped,
  `Mulheres, n` = nF, `Homens, n` = nM,
  `Taxa padr. por idade, mulheres (IC95%)` = txF, `Taxa padr. por idade, homens (IC95%)` = txM,
  `Razão mulher/homem (IC95%)` = razao)]

# ---------------------------------------------------------------- Figura 2
xper <- setNames(sapply(strsplit(PER, "-"), function(z) mean(as.numeric(z))), PER)
# mesma paleta de scripts/comum.R
cores <- c(Brasil = "#0b0b0b", Norte = "#2a78d6", Nordeste = "#eb6834", Sudeste = "#1baf7a", Sul = "#eda100", `Centro-Oeste` = "#e87ba4")
fa <- tx_reg[periodo != PER_TOT][, x := xper[periodo]][, local := factor(local, levels = c("Brasil", REG))]
fb <- dist_per[periodo != PER_TOT][, x := xper[periodo]][, local := factor(local, levels = c("Brasil", REG))]
dg <- position_dodge(width = 1.6)
pA <- ggplot(fa, aes(x, dsr, colour = local, group = local)) +
  geom_line(position = dg, linewidth = 0.5, alpha = 0.7) + geom_pointrange(aes(ymin = dsr_lo, ymax = dsr_hi), position = dg, size = 0.3) +
  geom_text(aes(y = dsr_hi, label = n), position = dg, vjust = -0.6, size = 2.3, show.legend = FALSE) +
  scale_colour_manual(values = cores, name = "Região de residência") + guides(colour = guide_legend(nrow = 1)) +
  scale_x_continuous(breaks = xper, labels = names(xper), limits = c(INI, 2025.5)) +
  labs(x = NULL, y = "Transplantes por milhão/ano\n(padronizada por idade e sexo; IC95%)",
       title = "A. Taxa de transplante cardíaco por região de residência", subtitle = "Números = transplantes no período") +
  theme_minimal(base_size = 10) + theme(legend.position = "bottom", panel.grid.minor = element_blank())
pB <- ggplot(fb, aes(x, mediana, colour = local, group = local)) +
  geom_line(position = dg, linewidth = 0.5, alpha = 0.7) + geom_point(position = dg, size = 1.8) +
  geom_linerange(aes(ymin = mediana, ymax = P75), position = dg, linewidth = 0.4) +
  scale_colour_manual(values = cores, name = "Região de residência", guide = "none") +
  scale_x_continuous(breaks = xper, labels = names(xper), limits = c(INI, 2025.5)) +
  scale_y_continuous(trans = scales::pseudo_log_trans(sigma = 10, base = 10), breaks = c(0, 10, 30, 100, 300, 1000, 3000)) +
  labs(x = "Período de internação", y = "Distância percorrida, km (escala pseudo-log)\n(ponto = mediana; barra até P75)",
       title = "B. Distância entre município de residência e do hospital", subtitle = "Mesmos transplantes do painel A") +
  theme_minimal(base_size = 10) + theme(legend.position = "bottom", panel.grid.minor = element_blank())
fig2 <- pA / pB
ggsave(file.path(out, "Figura2_taxa_distancia.png"), fig2, width = 8.5, height = 9, dpi = 200, bg = "white")

fs <- prox_ano[, .(ano, local = factor(local, levels = c("Brasil", REG)), limiar = paste0("Centro ativo com ≥", limiar, " TxC/ano"), le300, le500, le1000)]
fs <- melt(fs, id.vars = c("ano", "local", "limiar"), variable.name = "raio", value.name = "pct")
fs[, raio := factor(raio, levels = c("le300", "le500", "le1000"), labels = c("≤300 km", "≤500 km", "≤1.000 km"))]
pS <- ggplot(fs, aes(ano, pct, colour = local)) + geom_line() + geom_point(size = 0.8) + facet_grid(limiar ~ raio) +
  scale_colour_manual(values = cores, name = "Região de residência") + scale_y_continuous(limits = c(0, 100)) +
  labs(x = "Ano", y = "% da população (Censo 2022) a até X km\nde um centro ativo (geodésica, sede a sede)",
       title = "Proximidade geográfica potencial a um centro de transplante cardíaco ativo") +
  theme_minimal(base_size = 9) + theme(legend.position = "bottom", panel.grid.minor = element_blank())
ggsave(file.path(out, "FiguraS2_proximidade.png"), pS, width = 9, height = 6, dpi = 200, bg = "white")

fr <- ry[, .(regiao, ano, n, pop, obs = n / pop * 1e6, pred, pred_lo, pred_hi)]
pT <- ggplot(fr, aes(ano)) + geom_ribbon(aes(ymin = pred_lo, ymax = pred_hi), alpha = 0.2) + geom_line(aes(y = pred)) +
  geom_point(aes(y = obs), size = 1) + geom_text(aes(y = obs, label = n), vjust = -0.7, size = 2) +
  facet_wrap(~ factor(regiao, levels = REG), nrow = 1) +
  labs(x = "Ano", y = "Transplantes por milhão (taxa bruta)", title = "Tendência por região de residência: observado (pontos, n) e modelo de contagem (linha, IC95%)") +
  theme_minimal(base_size = 9) + theme(panel.grid.minor = element_blank(), axis.text.x = element_text(angle = 90, vjust = 0.5))
ggsave(file.path(out, "FiguraS2_tendencia_regiao.png"), pT, width = 11, height = 3.6, dpi = 200, bg = "white")

# ---------------------------------------------------------------- saída
fwrite(Tabela3, file.path(out, "Tabela3.csv"), bom = TRUE)
fwrite(Tabela5, file.path(out, "Tabela5.csv"), bom = TRUE)
wb <- createWorkbook()
sheets <- list(Tabela3 = Tabela3, Tabela5 = Tabela5, Taxa_regiao_periodo = tx_reg, Taxa_UF_periodo = tx_uf,
  Tendencia_regiao_IRR = tend, Tendencia_regiao_ajustado = ry,
  Dispersao = data.table(modelo = "região × ano", pearson_gl = dt1$pearson_gl, LRT = dt1$lrt, p = dt1$p, familia = if (usa_nb) "BN" else "Poisson", KS_residuos_p = ks1$p.value),
  Modelo_UF = if (is.null(uf_res_mod)) data.table(resultado = "não atendeu B5; só descritivo") else uf_res_mod,
  Proximidade_ano = prox_ano, Proximidade_periodo = prox_per, Distancia_ano = dist_ano, Distancia_periodo = dist_per,
  ForaUF_Firth = fora_mod, Casos_MS_SE_MA = casos3, Criancas_taxa = kid_tx, Criancas_vs_adultos = kid_vs_ad,
  Centros_pediatricos_ano = ped_cent, Mulheres_taxa = mulh, Mulheres_tendencia = mulh_tend, Mulheres_ano = mulh_ano)
for (s in names(sheets)) { addWorksheet(wb, s); writeData(wb, s, sheets[[s]]) }
saveWorkbook(wb, file.path(out, "Bloco2_tabelas.xlsx"), overwrite = TRUE)
fwrite(tx_reg, file.path(out, "conf_taxa_regiao.csv")); fwrite(prox_ano, file.path(out, "conf_proximidade_ano.csv"))
cat("\nArquivos em", out, ":\n"); print(list.files(out))
sink()
writeLines(capture.output(sessionInfo()), file.path(dirname(out), "sessionInfo.txt"))
