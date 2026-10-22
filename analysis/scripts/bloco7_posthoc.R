# Bloco 7 — Análises post hoc, descritivas ou de sensibilidade: origem do crescimento, fluxos entre regiões, centros do RJ,
# completude de 2025, componentes do reembolso, UTI e pandemia
# Uso: LANG=C.UTF-8 Rscript scripts/bloco7_posthoc.R data_2000_w04 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; outs <- if (length(args) >= 2) args[2] else "outputs"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
out <- file.path(outs, "bloco7"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco7.txt"), split = TRUE)
cat("Bloco 7 (post hoc) —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d; ca <- L$ca
rbt <- fread(file.path(base, "rbt/rbt_coracao_uf.csv"))

# ================================================================ Decomposição do crescimento
ult <- ca[n_txc > 0, .(ultimo = max(ano)), by = centro]
grp <- merge(unique(ca[, .(centro, tipo_centro)]), ult, by = "centro")
G_ENT <- paste("Centros com", LAB_ENT); G_ATV <- paste(LAB_INC, "ainda ativos em 2024–25"); G_SEM <- paste(LAB_INC, "sem atividade em 2024–25")
grp[, grupo := fifelse(tipo_centro == "entrante", G_ENT, fifelse(ultimo >= 2024, G_ATV, G_SEM))]
d <- merge(d, grp[, .(centro, grupo)], by = "centro")
cres_ano <- dcast(d[, .N, by = .(ano, grupo)], ano ~ grupo, value.var = "N", fill = 0)
J0 <- sprintf("media_%d_%02d", INI, (INI + 1) %% 100)
dec <- d[ano %in% c(INI, INI + 1, 2024, 2025), .(AIH_ano = .N / 2), by = .(janela = fifelse(ano <= INI + 1, J0, "media_2024_25"), grupo)]
dec <- dcast(dec, grupo ~ janela, value.var = "AIH_ano", fill = 0)
dec[, variacao := media_2024_25 - get(J0)]; dec[, pct_da_variacao := 100 * variacao / sum(variacao)]
dec <- merge(dec, grp[, .(centros = .N), by = grupo], by = "grupo")
tot <- dec[, .(grupo = "Total", m0 = sum(get(J0)), media_2024_25 = sum(media_2024_25), variacao = sum(variacao), pct_da_variacao = 100, centros = sum(centros))]
setnames(tot, "m0", J0); dec <- rbind(dec, tot, use.names = TRUE)
cat("\n== Média anual de AIH,", sprintf("%d–%02d", INI, (INI + 1) %% 100), "× 2024–25, por grupo de centro\n"); print(dec)
fc <- melt(cres_ano, id.vars = "ano", variable.name = "grupo", value.name = "AIH")
fc[, grupo := factor(grupo, levels = c(G_ATV, G_SEM, G_ENT))]
p5 <- ggplot(fc, aes(ano, AIH, colour = grupo)) + geom_line(linewidth = 0.8) + geom_point(size = 1.6) +
  scale_colour_manual(values = PAL[1:3], name = NULL) + guides(colour = guide_legend(ncol = 1)) +
  labs(x = "Ano de internação", y = "AIH de TxC no ano", title = "De onde veio o crescimento: AIH por grupo de centro (rede observada no SIH)",
       subtitle = "Post hoc, descritivo") + tema
ggsave(file.path(out, "FiguraR5_crescimento_por_grupo.png"), p5, width = 8, height = 4.8, dpi = 200, bg = "white")

# ================================================================ Fluxos
flu_reg <- dcast(d[, .N, by = .(regiao_res, regiao_hosp)], regiao_res ~ regiao_hosp, value.var = "N", fill = 0)
flu_reg[, Total := rowSums(.SD), .SDcols = -"regiao_res"]
norte <- d[regiao_res == "Norte", .N, by = .(uf_res, uf_hosp, regiao_hosp)][order(uf_res, -N)]
fora <- d[fora_uf %in% 1, .N, by = .(uf_res, uf_hosp)][order(-N)]
cat("\n== Região de residência × região do hospital\n"); print(flu_reg)
cat("\nResidentes da Região Norte: UF de residência → UF do hospital\n"); print(norte)
cat("\nPrincipais fluxos interestaduais (n ≥ 10):\n"); print(fora[N >= 10])

# ================================================================ Auditoria descritiva dos centros do RJ
rj_ids <- d[uf_hosp == "RJ", .N, by = centro][order(-N)]$centro   # rótulo local (RJ-A, RJ-B), sem o ID global, para não cruzar com outras tabelas
d[, grupo_rj := fifelse(uf_hosp == "RJ", paste0("RJ-", LETTERS[match(centro, rj_ids)]), "Demais UFs")]
aud <- function(x) x[, .(AIH = .N, obitos = sum(morte), mort_pct = 100 * mean(morte), O_E = sum(morte) / sum(p_risco),
  idade_mediana = as.numeric(median(idade)), pct_60mais = 100 * mean(idade >= 60), pct_mulher = 100 * mean(sexo == "F"), pct_ped = 100 * mean(idade < 18),
  pct_urgencia = 100 * mean(carater == "urgencia_outros"), perm_mediana = as.numeric(median(dias_perm)), uti_mediana = as.numeric(median(uti_dias)),
  pct_uti_0 = 100 * mean(uti_dias == 0), obito_ate_1dia_pct_dos_obitos = 100 * sum(morte == 1 & dias_perm <= 1) / max(sum(morte), 1),
  V_mediano = as.numeric(median(V)), anos = paste(range(ano), collapse = "–"), pct_I50 = 100 * mean(substr(diag_princ, 1, 3) == "I50"))]
rj <- rbind(d[, aud(.SD), by = grupo_rj], aud(d[uf_hosp != "RJ"])[, grupo_rj := "Demais UFs (conferência)"], fill = TRUE)
rj <- rj[grupo_rj != "Demais UFs (conferência)"]
rj_per <- d[uf_hosp == "RJ", .(AIH = .N, obitos = sum(morte), mort_pct = 100 * mean(morte)), by = .(periodo)][order(periodo)]
rj_rbt <- merge(d[uf_hosp == "RJ" & ano %in% c(2020, 2023, 2024), .(SIH = .N, obitos_SIH = sum(morte)), by = ano], rbt[uf == "RJ", .(ano, RBT = rbt_txc)], by = "ano", all = TRUE)
cat("\n== Auditoria descritiva — centros do RJ × demais UFs (sem leitura de desempenho)\n"); print(rj); print(rj_per); print(rj_rbt)

# ================================================================ Base de datas e completude de 2025
datas <- merge(merge(d[, .(internacao = .N), by = .(ano = ano_inter)], d[, .(saida = .N), by = .(ano = ano_saida)], all = TRUE),
               d[, .(competencia = .N), by = .(ano = competencia %/% 100)], all = TRUE)
d[, atraso := (competencia %/% 100 - ano_inter) * 12 + (competencia %% 100 - mes_inter)]
comp_max <- max(d$competencia); jan_max <- (comp_max %/% 100) * 12 + comp_max %% 100
hist <- d[ano_inter %in% 2015:2023]   # atraso observado em anos completos
completude <- rbindlist(lapply(c(2024, 2025), function(a) {
  x <- d[ano_inter == a, .(obs = .N), by = mes_inter]
  x[, janela := jan_max - (a * 12 + mes_inter)]
  x[, p_proc := sapply(janela, function(w) mean(hist$atraso <= w))]
  data.table(ano = a, AIH_observadas = sum(x$obs), completude_esperada_pct = 100 * sum(x$obs) / sum(x$obs / x$p_proc),
             AIH_ainda_nao_processadas_estimadas = sum(x$obs / x$p_proc) - sum(x$obs))
}))
atraso_dist <- hist[, .(AIH = .N), by = .(atraso_meses = pmin(atraso, 13))][order(atraso_meses)][, pct_acum := 100 * cumsum(AIH) / sum(AIH)]
cat("\n== AIH por ano segundo a base de datas\n"); print(datas[ano >= 2023])
cat("Competência máxima do banco:", comp_max, "\nAtraso internação → competência (AIH de 2015–2023):\n"); print(atraso_dist)
cat("Completude esperada (supondo o mesmo atraso dos anos anteriores):\n"); print(completude)

# ================================================================ Componentes do reembolso
d[, fator := val_tot_real_dez2025 / val_tot]
d[, `:=`(sh_real = val_sh * fator, sp_real = val_sp * fator)]
ree <- d[, .(AIH = .N, total_mediana = median(val_tot_real_dez2025), SH_mediana = median(sh_real), SP_mediana = median(sp_real),
             pct_SH_no_total = 100 * sum(sh_real) / sum(val_tot_real_dez2025), soma_SH_SP_igual_total_pct = 100 * mean(abs(val_sh + val_sp - val_tot) < 0.01)), by = ano][order(ano)]
cat("\n== Componentes do valor por AIH (R$ dez/2025)\n"); print(ree)
fr <- melt(ree[, .(ano, `Total` = total_mediana, `Serviços hospitalares` = SH_mediana, `Serviços profissionais` = SP_mediana)], id.vars = "ano")
p9 <- ggplot(fr, aes(ano, value / 1000, colour = variable)) + geom_line(linewidth = 0.8) + geom_point(size = 1.4) +
  scale_colour_manual(values = PAL[1:3], name = NULL) + scale_y_continuous(limits = c(0, NA)) +
  labs(x = "Ano", y = "Mediana por AIH, R$ mil (dez/2025)", title = "Componentes do valor da AIH de TxC (IPCA, R$ de dez/2025)", subtitle = "Post hoc, descritivo") + tema
ggsave(file.path(out, "FiguraR9_reembolso_componentes.png"), p9, width = 8, height = 4.2, dpi = 200, bg = "white")

# ================================================================ UTI (descritivo; não entra no ajuste)
uti <- rbind(d[, .(grupo = "Todos", AIH = .N, uti_mediana = as.numeric(median(uti_dias)), uti_P25 = as.numeric(quantile(uti_dias, .25)), uti_P75 = as.numeric(quantile(uti_dias, .75)), pct_uti_0 = 100 * mean(uti_dias == 0)), by = .(periodo = as.character(periodo))],
             d[, .(AIH = .N, uti_mediana = as.numeric(median(uti_dias)), uti_P25 = as.numeric(quantile(uti_dias, .25)), uti_P75 = as.numeric(quantile(uti_dias, .75)), pct_uti_0 = 100 * mean(uti_dias == 0)),
               by = .(grupo = fifelse(morte == 1, "Óbito hospitalar", "Alta"), periodo = as.character(periodo))])
cat("\n== Dias de UTI registrados na AIH\n"); print(uti[order(grupo, periodo)])

# ================================================================ Pandemia: pré-janelas e placebo
ms <- CJ(ano = 2013:2025, mes = 1:12)
ms <- merge(ms, d[, .(n = .N), by = .(ano, mes = mes_inter)], all.x = TRUE)[is.na(n), n := 0L]
ms[, data := as.Date(sprintf("%d-%02d-01", ano, mes))]
its <- function(inicio, quebra = as.Date("2020-03-01"), fim = as.Date("2025-12-01")) {
  x <- ms[data >= inicio & data <= fim][, t := seq_len(.N)]
  x[, `:=`(degrau = as.integer(data >= quebra), s1 = sin(2 * pi * mes / 12), c1 = cos(2 * pi * mes / 12))]
  x[, t_pos := pmax(0, t - x[data == quebra, t] + 1) * degrau]
  m <- glm(n ~ t + s1 + c1 + degrau + t_pos, family = quasipoisson, data = x); ci <- confint.default(m)
  data.table(inicio = format(inicio, "%Y-%m"), quebra = format(quebra, "%Y-%m"), fim = format(fim, "%Y-%m"), meses = nrow(x),
             RR_degrau = exp(coef(m)["degrau"]), lo = exp(ci["degrau", 1]), hi = exp(ci["degrau", 2]),
             mudanca_inclinacao_mensal = exp(coef(m)["t_pos"]), incl_lo = exp(ci["t_pos", 1]), incl_hi = exp(ci["t_pos", 2]), dispersao = summary(m)$dispersion)
}
pan <- rbind(its(as.Date("2013-01-01")), its(as.Date("2015-01-01")), its(as.Date("2017-01-01")),
             its(as.Date("2015-01-01"), quebra = as.Date("2019-03-01"), fim = as.Date("2020-02-01")))
pan[, analise := c("Pré-janela desde 2013", "Pré-janela desde 2015 (principal, Tabela S9)", "Pré-janela desde 2017", "Placebo: degrau em mar/2019, só período pré-pandemia")]
pre <- ms[data >= as.Date("2015-01-01") & data <= as.Date("2020-02-01")][, t := seq_len(.N)][, `:=`(s1 = sin(2 * pi * mes / 12), c1 = cos(2 * pi * mes / 12))]
m_lin <- glm(n ~ t + s1 + c1, family = quasipoisson, data = pre); m_ns <- glm(n ~ ns(t, 2) + s1 + c1, family = quasipoisson, data = pre)
pre_teste <- data.table(teste = "Não linearidade da tendência pré-pandemia (jan/2015–fev/2020): ns(t, 2) × linear", p_F = anova(m_lin, m_ns, test = "F")$`Pr(>F)`[2])
cat("\n== Pandemia: sensibilidade à pré-janela e placebo\n"); print(pan); print(pre_teste)

salva_xlsx(list(R5_decomposicao = dec, R5_por_ano = cres_ano, R6_regiao = flu_reg, R6_Norte = norte, R6_fluxos_UF = fora,
                R7_RJ = rj, R7_RJ_periodo = rj_per, R7_RJ_RBT = rj_rbt, R8_bases_data = datas, R8_atraso = atraso_dist, R8_completude = completude,
                R9_reembolso = ree, R10_UTI = uti, R11_pandemia = pan, R11_pre_tendencia = pre_teste), file.path(out, "Bloco7_posthoc.xlsx"))
cat("\nArquivos:", paste(list.files(out), collapse = ", "), "\n")
sink()
