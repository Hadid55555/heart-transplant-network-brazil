# Bloco 5 — Síntese descritiva por ano, período e região (lê as saídas dos blocos 1 e 2)
# Uso: LANG=C.UTF-8 Rscript scripts/bloco5_sintese.R data_2000_w04 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; outs <- if (length(args) >= 2) args[2] else "outputs"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
out <- file.path(outs, "bloco5"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_bloco5.txt"), split = TRUE)
cat("Bloco 5 —", format(Sys.time(), "%Y-%m-%d %H:%M"), "\n")
L <- carrega(base); d <- L$d; ca <- L$ca
pop <- fread(file.path(base, "ibge_covariaveis/pop_uf_ano_sexo_idade.csv"))[tipo_faixa == "analise"]

# ---------------------------------------------------------------- Figura 4
rede <- d[, .(AIH = .N, n_lt10 = sum(V < 10), n_entr = sum(entrante)), by = ano][order(ano)]
rede[, `:=`(pct_lt10 = 100 * n_lt10 / AIH, pct_entr = 100 * n_entr / AIH)]
pad <- pop[ano == 2025, .(p = sum(populacao)), by = .(faixa_etaria, sexo)][, w := p / sum(p)]
dsr_ano <- rbindlist(lapply(ANOS, function(a) {
  x <- d[ano == a, .(x = .N), by = .(faixa_etaria, sexo)]
  s <- merge(merge(pad, pop[ano == a, .(py = sum(populacao)), by = .(faixa_etaria, sexo)], by = c("faixa_etaria", "sexo")),
             x, by = c("faixa_etaria", "sexo"), all.x = TRUE)[is.na(x), x := 0L]
  r <- sum(s$w * s$x / s$py); v <- sum(s$w^2 * s$x / s$py^2); wm <- max(s$w / s$py)
  data.table(ano = a, n = sum(s$x), dsr = 1e6 * r, lo = 1e6 * v / (2 * r) * qchisq(.025, 2 * r^2 / v),
             hi = 1e6 * (v + wm^2) / (2 * (r + wm)) * qchisq(.975, 2 * (r + wm)^2 / (v + wm^2)))
}))
prox <- fread(file.path(outs, "bloco2/conf_proximidade_ano.csv"))[local == "Brasil"]
t2 <- fread(file.path(outs, "bloco1/Tabela2.csv"))
stopifnot(all.equal(round(rede$pct_lt10, 1), t2$AIH_em_centros_lt10_pct))   # conferência com o bloco 1
fa <- melt(rede[, .(ano, `Centros com <10 TxC no ano` = pct_lt10, pct_entr)], id.vars = "ano")
levels(fa$variable)[2] <- paste0("Centros com 1º TxC observado ≥", ENT)
pA <- ggplot(fa, aes(ano, value, colour = variable)) + geom_line() + geom_point(size = 1.5) +
  scale_colour_manual(values = PAL[1:2], name = NULL) + scale_y_continuous(limits = c(0, NA)) +
  labs(x = NULL, y = "% dos transplantes do ano", title = "A. Onde os transplantes foram feitos") + tema
pB <- ggplot(dsr_ano, aes(ano, dsr)) + geom_ribbon(aes(ymin = lo, ymax = hi), fill = "grey85") + geom_line() + geom_point(size = 1.5) +
  geom_text(aes(y = hi, label = n), vjust = -0.5, size = 2.4) + scale_y_continuous(limits = c(0, NA), expand = expansion(mult = c(0, 0.12))) +
  labs(x = NULL, y = "TxC por milhão\n(padronizada; IC95%)", title = "B. Taxa nacional padronizada por idade e sexo (números = TxC no ano)") + tema
fc <- prox[, .(ano, limiar = paste0("Centro ativo com ≥", limiar, " TxC/ano"), le500)]
pC <- ggplot(fc, aes(ano, le500, linetype = limiar)) + geom_line() + geom_point(size = 1.5) + scale_y_continuous(limits = c(50, 100)) +
  labs(x = "Ano", y = "% da população\na ≤500 km", linetype = NULL, title = "C. Proximidade geográfica potencial (Censo 2022, geodésica sede a sede)") + tema
ggsave(file.path(out, "Figura4_sintese.png"), pA / pB / pC, width = 8, height = 9.5, dpi = 200, bg = "white")

# ---------------------------------------------------------------- tabela período × região
crude <- mean(d$morte)
oe <- function(dd) { O <- sum(dd$morte); E <- sum(dd$p_risco)
  lo <- if (O == 0) 0 else qchisq(.025, 2 * O) / 2; hi <- qchisq(.975, 2 * O + 2) / 2
  list(N = nrow(dd), O = O, E = E, adj = 100 * crude * O / E, lo = 100 * crude * lo / E, hi = 100 * crude * hi / E) }
mv <- rbind(d[, oe(.SD), by = .(grupo = as.character(periodo), Vcat)][, nivel := "Brasil"],
            d[, oe(.SD), by = .(grupo = regiao_hosp, Vcat)][, nivel := paste0("Região do hospital (", PER_TOT_TXT, ")")])
mv[, cel := paste0(fmt(adj, 1), " (", fmt(lo, 1), "–", fmt(hi, 1), ") [", O, "/", N, "]")]
mvw <- dcast(mv, nivel + grupo ~ Vcat, value.var = "cel", fill = "—")
tx <- fread(file.path(outs, "bloco2/conf_taxa_regiao.csv"))
dist <- as.data.table(read.xlsx(file.path(outs, "bloco2/Bloco2_tabelas.xlsx"), sheet = "Distancia_periodo"))
uso <- merge(tx[, .(grupo = fifelse(local == "Brasil", periodo, local), local, periodo, n, dsr = ic(dsr, dsr_lo, dsr_hi))],
             dist[, .(local, periodo, distancia = paste0(fmt(mediana, 0), " (", fmt(P75, 0), ")"))], by = c("local", "periodo"))
uso <- uso[(local == "Brasil" & periodo != PER_TOT) | (local != "Brasil" & periodo == PER_TOT)]
TabelaS5 <- merge(uso[, .(grupo, `TxC por residência, n` = n, `Taxa padronizada/milhão/ano (IC95%)` = dsr, `Distância, km, mediana (P75)` = distancia)],
                  mvw, by = "grupo", all = TRUE)
for (v in c("<10", "10-19", "20-39", ">=40")) set(TabelaS5, which(is.na(TabelaS5[[v]])), v, "sem centro na região")
TabelaS5[, ord := match(grupo, c(PER, REG))]; setorder(TabelaS5, ord); TabelaS5[, ord := NULL]
TabelaS5[, nivel := fifelse(grupo %in% PER, "Brasil, por período", paste0("Região (", PER_TOT_TXT, "): residência p/ utilização; hospital p/ óbito"))]
setcolorder(TabelaS5, c("nivel", "grupo")); setnames(TabelaS5, c("nivel", "grupo"), c("Nível", "Período / região"))
setnames(TabelaS5, c("<10", "10-19", "20-39", ">=40"), paste0("Óbito ajustado %, V ", c("<10", "10–19", "20–39", "≥40"), " (IC95%) [óbitos/AIH]"))
cat("\n== Tabela síntese (utilização por residência; mortalidade por padronização indireta por categoria de V)\n"); print(TabelaS5)

# ---------------------------------------------------------------- fora × dentro da UF
cat("\n== Mortalidade fora × dentro da UF (descritiva, sujeita a seleção)\n")
df_ <- d[!is.na(fora_uf)]   # exclui as 15 AIH sem município de residência
ff <- escada(morte ~ fora_uf + faixa5 + sexoF + a1 + a2 + (1 | centro), df_, NULL, "fora da UF")
fora <- cbind(or_tab(ff, "fora_uf"), df_[, oe(.SD), by = fora_uf][order(fora_uf)][, .(grupo = c("Dentro da UF", "Fora da UF"), N, O, adj, lo, hi)] |> (\(x) data.table(dentro = x[1, paste0(fmt(adj, 1), "% [", O, "/", N, "]")], fora = x[2, paste0(fmt(adj, 1), "% [", O, "/", N, "]")]))())
print(fora)
fwrite(TabelaS5, file.path(out, "Tabela_sintese_periodo_regiao.csv"), bom = TRUE)
salva_xlsx(list(Tabela_sintese = TabelaS5, Mort_O_E = mv, Figura4_A = rede, Figura4_B = dsr_ano, Figura4_C = fc, Fora_UF = fora), file.path(out, "Bloco5_tabelas.xlsx"))
cat("\nArquivos:", paste(list.files(out), collapse = ", "), "\n")
sink()
