# Post hoc: sensibilidades adicionais do termo "dentro do centro" (mesmo modelo de volume).
# (d) só centros com ≥5 anos consecutivos de atividade; (e) por porte do centro (média de V no período <10 vs ≥10 TxC/ano):
#     interação dentro × porte; (f) média do centro sem ponderação por AIH (média simples dos anos ativos) — já na Tabela S2, repetida aqui.
# Uso: LANG=C.UTF-8 TXC_INI=2000 Rscript scripts/posthoc_dentro_2.R data_2000 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data_2000"; outs <- if (length(args) >= 2) args[2] else "outputs_2000_2025"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
out <- file.path(outs, "posthoc"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_posthoc_dentro_2.txt"), split = TRUE)
L <- carrega(base); d <- L$d; ca <- L$ca
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9)))
aj <- "+ faixa5 + sexoF + a1 + a2 + (1 | centro)"
prep <- function(x) { x <- copy(x); x[, centro := droplevels(centro)]; x[, entre := mean(Vm1), by = centro]; x[, dentro10 := (Vm1 - entre) / 10]; add_rcs(x, "entre", kE, "e"); x }
res <- list()
f0 <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10", aj)), prep(d), NULL, "principal")
res[["Principal (referência)"]] <- or_tab(f0, "dentro10")[, `:=`(n_AIH = nrow(d), centros = uniqueN(d$centro), passo = f0$passo)]
# (d) ≥5 anos consecutivos
run <- ca[n_txc > 0][order(centro, ano)][, g := cumsum(c(1, diff(ano) != 1)), by = centro][, .N, by = .(centro, g)][, .(max_seq = max(N)), by = centro]
c5 <- run[max_seq >= 5, centro]; x5 <- prep(d[centro %in% c5])
fd <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10", aj)), x5, as.formula(paste("morte ~ e1 + dentro10", aj)), "≥5 anos consecutivos")
res[["(d) Só centros com ≥5 anos consecutivos de atividade"]] <- or_tab(fd, "dentro10")[, `:=`(n_AIH = nrow(x5), centros = uniqueN(x5$centro), passo = fd$passo)]
# (e) porte: média anual de TxC do centro nos anos ativos (sem ponderar por AIH)
porte <- ca[n_txc > 0, .(media_ano = mean(n_txc)), by = centro]
xm <- merge(d, porte, by = "centro"); xm[, centro := factor(centro)]; xe <- prep(xm); xe[, grande := as.integer(media_ano >= 10)]
fe <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10 * grande", aj)), xe, NULL, "dentro × porte")
nb <- nomes_b(fe)
L2 <- rbind(`dentro, centros com média <10 TxC/ano` = setNames(as.numeric(nb == "dentro10"), nb),
            `dentro, centros com média ≥10 TxC/ano` = setNames(as.numeric(nb %in% c("dentro10", "dentro10:grande")), nb),
            `razão (≥10 ÷ <10)` = setNames(as.numeric(nb == "dentro10:grande"), nb))
ce <- or_contraste(fe, L2, rownames(L2))
tab <- rbind(rbindlist(lapply(names(res), function(n) res[[n]][, analise := n]), use.names = TRUE)[, .(analise, OR, lo, hi, p, n_AIH, centros, passo)],
             ce[, .(analise = paste("(e)", contraste), OR, lo, hi, p, n_AIH = nrow(xe), centros = uniqueN(xe$centro), passo = fe$passo)])
cat("\nCentros com média ≥10 TxC/ano:", porte[media_ano >= 10, .N], "de", nrow(porte), "| AIH nesses centros:", xe[grande == 1, .N], "\n")
print(tab[, .(analise, OR = round(OR, 3), lo = round(lo, 3), hi = round(hi, 3), p = signif(p, 3), n_AIH, centros, passo)])
fwrite(tab, file.path(out, "posthoc_dentro_2.csv"), bom = TRUE)
sink()
