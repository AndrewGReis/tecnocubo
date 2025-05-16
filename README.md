# 🕷️ Web Scraper - Tecnocubo (Impressoras 3D)

Automação para coleta de preços e disponibilidade de produtos na loja [Tecnocubo](https://www.tecnocubo.com.br), com registro em planilha e prints de evidência.

# 🔎 Referência de busca:
https://www.tecnocubo.com.br/impressoras/bambu-lab/impressora-3d-bambu-lab-x1-carbon-combo

## ⚙️ Funcionalidades
- **🌐 Navegação automatizada** via Selenium  
- **✖️ Fechamento inteligente** de pop-ups
- **📦 Extração de dados**: 
  - Nome do produto
  - Preço após adição no carrinho
  - URL do produto


## 📊 Estrutura de execução   
O código abre automaticamente a página, fecha o pop up, navega da página, clica no adicionar ao carrinho,cria uma pasta de print, tira print do insumo no carrinho, salva a print na pasta, cria um arquivo csv, salva no arquivo csv as informações:
URL, nome_produto, preco_desconto, data_coleta.
Após isso, remove o item do carrinho, fecha o pop up docarrinho e encerra o navegador.

- ** 📸 Captura de evidências**:
  - Screenshots do produto no carrinho
  - HTML da página (em caso de erro)
- Exportação para Excel/XLSX
- Sistema de logging detalhado

## 🗒️ Destaques  
- **🤖 100% automatizado**  
- **📝 Logging detalhado** (arquivo + console)  
- **🔄 Pós-execução**: Limpeza automática do carrinho 
