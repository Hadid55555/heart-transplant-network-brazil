# Parâmetros da análise: série 2000–2025 (tabela SIH antiga 2000–2007 + SIGTAP 2008–2025).
INI <- as.integer(Sys.getenv("TXC_INI", "2000"))
ANOS <- INI:2025
ARQ_AIH <- sprintf("microdados/aih_txc_%d_2025.csv", INI)
PER_TOT <- sprintf("%d-2025", INI)
PER_TOT_TXT <- sprintf("%d–2025", INI)
PER <- c(if (INI < 2008) sprintf("%d-%d", seq(INI, 2004, 4), seq(INI + 3, 2007, 4)),
         "2008-2011", "2012-2015", "2016-2019", "2020-2022", "2023-2025")
CORTES <- c(if (INI < 2008) seq(INI - 1, 2003, 4), 2007, 2011, 2015, 2019, 2022, 2025)
periodo <- function(a) factor(cut(a, CORTES, labels = PER), levels = PER)
ENT <- as.integer(Sys.getenv("TXC_ENT", INI + 2))          # centro novo (entrante) = 1º TxC observado a partir de ENT. Análise principal: TXC_ENT=2004
# (observação inicial 2000–2003); o padrão INI + 2 (observação inicial 2000–2001) é a sensibilidade
LAB_ENT <- sprintf("1º TxC ≥%d", ENT)
LAB_INC <- sprintf("Centros %d–%02d", INI, (ENT - 1) %% 100)   # "Centros 2000–03"
LAB_INC_H <- sprintf("Centros %d-%02d", INI, (ENT - 1) %% 100) # "Centros 2000-03" (níveis de fator)
ESPERADO <- c(aih = 5821, obitos = 819, centros = 64)
confere_base <- function(d) stopifnot(all(d$tipo_centro == ifelse(d$ano_primeiro_txc_centro >= ENT, "entrante", "incumbente")),
                                      nrow(d) == ESPERADO[["aih"]], sum(d$morte) == ESPERADO[["obitos"]],
                                      data.table::uniqueN(d$centro) == ESPERADO[["centros"]])
