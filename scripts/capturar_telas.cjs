// Gera as capturas de tela do painel usadas no README (docs/img/).
//
// Pré-requisitos: Node 18+ com o pacote `playwright` e o painel rodando:
//   streamlit run app/painel.py --server.headless true --server.port 8599
//   node scripts/capturar_telas.cjs [url] [pasta_saida]
const { chromium } = require("playwright");

const url = process.argv[2] ?? "http://localhost:8599/";
const saida = process.argv[3] ?? "docs/img";
const abas = [
  ["Mapa", "painel-mapa.png"],
  ["Ranking", "painel-ranking.png"],
  ["Evolução", "painel-evolucao.png"],
  ["Investimento × IDEB", "painel-investimento-ideb.png"],
  ["Matrículas", "painel-matriculas.png"],
  ["Comparar", "painel-comparar.png"],
];

(async () => {
const navegador = await chromium.launch();
const pagina = await navegador.newPage({ viewport: { width: 1400, height: 1100 }, deviceScaleFactor: 1 });
await pagina.goto(url, { waitUntil: "networkidle" });
await pagina.getByRole("tab", { name: "Mapa" }).waitFor({ timeout: 120000 });
await pagina.waitForTimeout(3000);

for (const [nome, arquivo] of abas) {
  await pagina.getByRole("tab", { name: nome, exact: true }).click();
  await pagina.waitForTimeout(3500);
  const erros = await pagina.locator('[data-testid="stException"]').count();
  if (erros) throw new Error(`a aba ${nome} mostrou uma exceção`);
  // Ranking é muito alto (139 barras): captura só a área visível.
  const inteira = nome !== "Ranking";
  await pagina.screenshot({ path: `${saida}/${arquivo}`, fullPage: inteira });
  console.log("ok", arquivo);
}
await navegador.close();
})().catch((erro) => {
  console.error(erro);
  process.exit(1);
});
