# Post hoc: de onde vem a associação "dentro do centro"?
# (a) mesmo modelo principal do H1 restrito a 2000–2007; (b) principal + log2(anos de programa) [experiência; censura à esquerda
# nos centros ativos em 2000–01]; (c) principal + interação dentro × período (2000–2007 vs 2008–2025).
# Uso: LANG=C.UTF-8 TXC_INI=2000 Rscript scripts/posthoc_dentro.R data_2000 outputs_2000_2025
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data_2000"; outs <- if (length(args) >= 2) args[2] else "outputs_2000_2025"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
out <- file.path(outs, "posthoc"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
sink(file.path(out, "log_posthoc_dentro.txt"), split = TRUE)
L <- carrega(base); d <- L$d
kE <- as.numeric(quantile(d$entre, c(.1, .5, .9))); add_rcs(d, "entre", kE, "e")
aj <- "+ faixa5 + sexoF + a1 + a2 + (1 | centro)"
res <- list()
fit0 <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10", aj)), d, NULL, "principal (referência)")
res[["Principal 2000–2025 (referência)"]] <- or_tab(fit0, "dentro10")
x <- d[ano <= 2007]; x[, centro := droplevels(centro)]; x[, entre := mean(Vm1), by = centro]; x[, dentro10 := (Vm1 - entre) / 10]; add_rcs(x, "entre", kE, "e")
fa <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10", aj)), x, as.formula(paste("morte ~ e1 + dentro10", aj)), "só 2000–2007")
res[["(a) Só 2000–2007 (média do centro recalculada no período)"]] <- or_tab(fa, "dentro10")
d[, lprog := log2(ano_programa)]
fb <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10 + lprog", aj)), d, NULL, "+ log2(anos de programa)")
res[["(b) + log2(anos de programa): termo dentro"]] <- or_tab(fb, "dentro10")
res[["(b) + log2(anos de programa): por duplicação dos anos de programa"]] <- or_tab(fb, "lprog")
d[, antes08 := as.integer(ano <= 2007)]
fc <- escada(as.formula(paste("morte ~ e1 + e2 + dentro10 * antes08", aj)), d, NULL, "dentro × período")
L2 <- rbind(`dentro em 2008–2025` = setNames(as.numeric(nomes_b(fc) == "dentro10"), nomes_b(fc)),
            `dentro em 2000–2007` = setNames(as.numeric(nomes_b(fc) %in% c("dentro10", "dentro10:antes08")), nomes_b(fc)),
            `razão (2000–2007 ÷ 2008–2025)` = setNames(as.numeric(nomes_b(fc) == "dentro10:antes08"), nomes_b(fc)))
ct <- or_contraste(fc, L2, rownames(L2))
tab <- rbind(rbindlist(lapply(names(res), function(n) res[[n]][, analise := n]), use.names = TRUE)[, .(analise, termo, OR, lo, hi, p)],
             ct[, .(analise = paste("(c) Interação dentro × período:", contraste), termo = "dentro10", OR, lo, hi, p)])
tab[, n_AIH := c(nrow(d), nrow(x), nrow(d), nrow(d), rep(nrow(d), 3))]
tab[, passo := c(fit0$passo, fa$passo, fb$passo, fb$passo, rep(fc$passo, 3))]
print(tab[, .(analise, OR = round(OR, 3), lo = round(lo, 3), hi = round(hi, 3), p = signif(p, 3), n_AIH, passo)])
fwrite(tab, file.path(out, "posthoc_dentro.csv"), bom = TRUE)
sink()
