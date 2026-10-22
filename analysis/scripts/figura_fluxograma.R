# Fluxograma de seleção das AIH (RECORD 13.1). As etapas da extração (arquivos lidos, registros com o procedimento e AIH só
# solicitadas) vêm dos registros de cobertura de extraction/ (saida_txc/parciais/_cobertura.jsonl e saida_2000_2007/parciais/_cobertura.jsonl);
# a base de análise e as subamostras são contadas aqui. Uso: LANG=C.UTF-8 Rscript scripts/figura_fluxograma.R data_2000_w04 outputs_2000_2025/bloco1
args <- commandArgs(trailingOnly = TRUE)
base <- if (length(args) >= 1) args[1] else "data"; out <- if (length(args) >= 2) args[2] else "outputs/bloco1"
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "comum.R"))
L <- carrega(base); d <- L$d
# etapas da extração, competências jan/2000–jun/2026
ARQ_RD <- 8580L; ARQ_TOT <- 8586L; REG_RD <- 320383793     # arquivos RD lidos e esperados (27 UFs) e registros nos arquivos lidos
REG_TXC <- 6356L                            # registros com 46800018/47800011 ou 0505020041 em PROC_REA ou PROC_SOLIC
EXCL_SOLICITADO <- 374L                     # transplante só como procedimento solicitado
COMP_TXT <- "jan/2000–jun/2026"; COD_TXT <- "\n(46800018/47800011 até 2007; 0505020041 desde 2008)"
FORA_JANELA <- REG_TXC - EXCL_SOLICITADO - nrow(d)   # TxC realizado com internação fora da janela (por diferença)
n <- function(x) sapply(x, function(v) format(v, big.mark = ".", decimal.mark = ","))
cnt <- function(x) list(N = nrow(x), C = uniqueN(x$centro), O = sum(x$morte))
tot <- cnt(d)
rep_ids <- d[, .N, by = paciente_provavel_id][N > 1, paciente_provavel_id]
fun <- d[, .(O = sum(morte), E = sum(p_risco)), by = centro]
lim <- function(E, p) { r <- qpois(p, E); a <- (ppois(r, E) - p) / (ppois(r, E) - ppois(r - 1, E)); pmax((r - a) / E, 0) }
fun[, fora := O / E > lim(E, .999)]        # mesmo critério do bloco 6 (limite superior de 99,8%)
sub <- list(
  `Aprendizado (exploratório): centros com 1º TxC observado ≥ENT` = cnt(d[(entrante)]),
  `  sem o maior centro entrante` = cnt(d[(entrante) & centro != d[(entrante), .N, by = centro][which.max(N), centro]]),
  `Sensibilidade: só adultos (≥18 anos)` = cnt(d[idade >= 18]),
  `Sensibilidade: sem 2020–2021` = cnt(d[!ano_inter %in% 2020:2021]),
  `Sensibilidade: sem as NREP AIH de prováveis readmitidos` = cnt(d[!paciente_provavel_id %in% rep_ids]),
  `Sensibilidade: uma linha por paciente provável` = list(N = uniqueN(d$paciente_provavel_id), C = uniqueN(d$centro), O = NA),
  `Post hoc: sem os centros acima de 99,8% no funil` = cnt(d[!centro %in% fun[(fora), centro]]))
names(sub) <- sub("ENT", ENT, sub("NREP", d[paciente_provavel_id %in% rep_ids, .N], names(sub)))
stopifnot(tot$N == 5821, tot$O == 819, FORA_JANELA == 161L)
tab <- data.table(etapa = names(sub), AIH = sapply(sub, `[[`, "N"), centros = sapply(sub, `[[`, "C"), obitos = sapply(sub, `[[`, "O"))
fwrite(tab, file.path(out, "fluxograma_contagens.csv"))
fwrite(data.table(etapa = c("Arquivos RD lidos", "Registros nos arquivos lidos", "Registros com TxC realizado ou solicitado", "Excluídos: só solicitado",
                            "TxC realizado", paste0("Excluídos: internação fora de ", PER_TOT_TXT), "Base de análise"),
                  n = c(ARQ_RD, REG_RD, REG_TXC, EXCL_SOLICITADO, REG_TXC - EXCL_SOLICITADO, FORA_JANELA, nrow(d))),
       file.path(out, "fluxograma_etapas.csv"))
print(tab)

caixa <- function(x, y, w, h, txt, fill = "white", size = 3.1, hjust = 0.5)
  list(annotate("rect", xmin = x - w / 2, xmax = x + w / 2, ymin = y - h / 2, ymax = y + h / 2, fill = fill, colour = "grey30", linewidth = 0.4),
       annotate("text", x = if (hjust == 0) x - w / 2 + 0.15 else x, y = y, label = txt, size = size, hjust = hjust, lineheight = 1.05))
seta <- function(x0, y0, x1, y1) annotate("segment", x = x0, y = y0, xend = x1, yend = y1, linewidth = 0.4,
                                          arrow = arrow(length = unit(0.12, "cm"), type = "closed"))
sub_txt <- paste0("Subamostras analíticas (cada uma parte da base de análise; não são exclusões em série)\n\n", paste0(sprintf("%s: %s AIH, %s centros%s", tab$etapa, n(tab$AIH), tab$centros,
                          ifelse(is.na(tab$obitos), "", paste0(", ", n(tab$obitos), " óbitos"))), collapse = "\n"))
p <- ggplot() + xlim(0, 10) + ylim(0, 12.6) + theme_void() +
  caixa(3.6, 12.0, 6.6, 1.0, sprintf("Arquivos RD (AIH reduzida) do SIH/SUS, 27 UFs, competências %s:\n%s de %s arquivos lidos (%s registros)%s", COMP_TXT, n(ARQ_RD), n(ARQ_TOT), n(REG_RD), "")) +
  seta(3.6, 11.5, 3.6, 10.75) +
  caixa(3.6, 10.3, 6.6, 0.8, sprintf("Registros com transplante cardíaco %s\ncomo procedimento realizado ou solicitado: n = %s", COD_TXT, n(REG_TXC))) +
  seta(3.6, 9.9, 3.6, 8.75) + seta(3.6, 9.45, 7.0, 9.45) +
  caixa(8.4, 9.45, 2.9, 0.9, sprintf("Excluídas: %s\ntransplante só como procedimento\nsolicitado (não realizado)", n(EXCL_SOLICITADO)), fill = "grey95") +
  caixa(3.6, 8.35, 6.6, 0.7, sprintf("Transplante como procedimento realizado: n = %s", n(REG_TXC - EXCL_SOLICITADO))) +
  seta(3.6, 8.0, 3.6, 7.35) + seta(3.6, 7.75, 7.0, 7.75) +
  caixa(8.4, 7.75, 2.9, 0.9, sprintf("Excluídas: %s\ndata de internação fora de\n01/01/%d–31/12/2025", n(FORA_JANELA), INI), fill = "grey95") +
  caixa(3.6, 6.8, 6.6, 1.1, sprintf("Base de análise: %s AIH (internação do transplante)\n%s centros (CNES anonimizado) · %s óbitos hospitalares\nN_AIH repetido: 0 · IDENT 3 ou 5: 0 · %s prováveis pacientes com 2 AIH",
                                     n(tot$N), tot$C, n(tot$O), length(rep_ids)), fill = "#e8f0fb") +
  seta(3.6, 6.25, 3.6, 5.45) +
  caixa(3.6, 5.0, 6.6, 0.8, sprintf("Primário (descritivo) e H1 (volume × óbito): todas as %s AIH, %s centros", n(tot$N), tot$C)) +
  seta(3.6, 4.6, 3.6, 3.9) +
  caixa(5.0, 2.65, 9.6, 2.5, sub_txt, size = 2.8, hjust = 0) +
  annotate("text", x = 0.2, y = 0.95, hjust = 0, size = 2.5, colour = "grey30", lineheight = 1,
           label = sprintf("Fonte: espelho público healthbr-data (Parquet 1:1 dos .dbc do DATASUS; SHA-256 por arquivo). Faltam no espelho RR jan–mai/2000 e AP out/2007\n(UFs sem centro de TxC). Fora da janela: %d com internação antes de 2000 e %d depois de 2025 (por diferença: %s − %s − %s).", 12L, FORA_JANELA - 12L, n(REG_TXC), n(EXCL_SOLICITADO), n(nrow(d))))
ggsave(file.path(out, "Figura_fluxograma.png"), p, width = 9, height = 9.2, dpi = 200, bg = "white")
cat("Fluxograma escrito em", file.path(out, "Figura_fluxograma.png"), "\n")
