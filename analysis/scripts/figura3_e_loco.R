# Figura 3 (com o suporte por centro marcado) e figura do leave-one-centre-out, a partir das saídas do bloco 3.
# Uso: LANG=C.UTF-8 Rscript scripts/figura3_e_loco.R data_2000_w04 outputs_2000_2025/bloco3
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; out <- if (length(args) >= 2) args[2] else "outputs/bloco3"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
L <- carrega(base); d <- L$d
curvas <- as.data.table(read.xlsx(file.path(out, "Bloco3_tabelas.xlsx"), sheet = "Curvas_Figura3"))
loco <- as.data.table(read.xlsx(file.path(out, "Bloco3_tabelas.xlsx"), sheet = "LOCO"))
res <- as.data.table(read.xlsx(file.path(out, "Bloco3_tabelas.xlsx"), sheet = "ML_contrastes"))

cen <- d[, .(entre = entre[1], AIH = .N), by = centro][order(entre)]
seg <- sort(unique(cen$entre), decreasing = TRUE)[2]          # acima do 2º maior volume médio, a curva "entre" depende de 1 centro
xmax <- max(d$Vm1) + 1
crude <- d[, .(n = .N, ob = sum(morte)), by = .(Vg = pmin(5 * floor(Vm1 / 5), 60))][, mort := 100 * ob / n]
pA <- ggplot(curvas, aes(V_menos_1, est, colour = curva, fill = curva)) +
  annotate("rect", xmin = seg, xmax = max(cen$entre), ymin = -Inf, ymax = Inf, fill = "grey80", alpha = 0.45) +
  annotate("text", x = (seg + max(cen$entre)) / 2, y = Inf, vjust = 1.4, size = 2.7, label = "curva entre centros\nsustentada por 1 centro") +
  geom_ribbon(aes(ymin = lo, ymax = hi), alpha = 0.15, colour = NA) + geom_line(linewidth = 0.8) +
  geom_point(data = crude, aes(Vg + 2, mort, size = n), inherit.aes = FALSE, shape = 21, fill = "grey80", colour = "grey40") +
  scale_size_area(max_size = 5, name = "AIH (bruto, por faixa de 5)") +
  scale_colour_manual(values = PAL[1:2], name = NULL) + scale_fill_manual(values = PAL[1:2], name = NULL) +
  scale_x_continuous(limits = c(0, xmax)) +
  labs(x = NULL, y = "Óbito hospitalar ajustado, % (IC95%)",
       title = "A. Mortalidade hospitalar ajustada × volume anual do centro sem o caso índice (V − 1)",
       subtitle = "Ajuste: faixa etária, sexo, ano (spline); intercepto aleatório de centro. Círculos = mortalidade bruta") +
  tema + theme(legend.box = "vertical")
pC <- ggplot(cen, aes(entre, 1, size = AIH)) + geom_point(shape = 21, fill = PAL[2], colour = "grey30", alpha = 0.7) +
  scale_size_area(max_size = 6, name = "AIH do centro") + scale_x_continuous(limits = c(0, xmax)) + scale_y_continuous(breaks = NULL) +
  labs(x = NULL, y = NULL, title = sprintf("B. Volume médio de cada centro (%d centros; posição no eixo da curva entre centros)", nlevels(d$centro))) + tema
pB <- ggplot(d, aes(Vm1)) + geom_histogram(binwidth = 2, boundary = 0, fill = "grey60", colour = "white") +
  scale_x_continuous(limits = c(0, xmax)) + labs(x = "V − 1 (outros transplantes do centro no ano)", y = "AIH, n", title = "C. Distribuição das AIH") + tema
ggsave(file.path(out, "Figura3_volume_mortalidade.png"), pA / pC / pB + plot_layout(heights = c(3, 0.6, 1)), width = 8.5, height = 9, dpi = 200, bg = "white")

ref <- res[match(unique(loco$contraste), contraste), .(contraste, OR)]
loco[, contraste_curto := fifelse(grepl("P10", contraste), "Entre: P10 vs P50", fifelse(grepl("P90", contraste), "Entre: P90 vs P50", "Dentro: +10 TxC/ano"))]
ref[, contraste_curto := fifelse(grepl("P10", contraste), "Entre: P10 vs P50", fifelse(grepl("P90", contraste), "Entre: P90 vs P50", "Dentro: +10 TxC/ano"))]
pL <- ggplot(loco, aes(OR, contraste_curto)) + geom_vline(xintercept = 1, linewidth = 0.3) +
  geom_jitter(height = 0.12, width = 0, colour = PAL[1], alpha = 0.6, size = 1.6) +
  geom_point(data = ref, aes(OR, contraste_curto), shape = 124, size = 8, colour = "#0b0b0b") +
  scale_x_log10() + labs(x = "OR ao retirar um centro por vez (escala log)", y = NULL,
  title = sprintf("Leave-one-centre-out do modelo principal do H1 (%d reajustes)", nlevels(d$centro)), subtitle = "Pontos = OR sem cada centro; traço preto = OR com todos os centros") + tema
ggsave(file.path(out, "FiguraS3_LOCO.png"), pL, width = 8, height = 3.6, dpi = 200, bg = "white")
cat("Figura 3 e Figura S3_LOCO escritas; 2º maior volume médio =", round(seg, 2), "; maior =", round(max(cen$entre), 2), "\n")
