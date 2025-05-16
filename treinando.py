import os
import time
import logging
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

class TecnoCuboSpider:
    def __init__(self):
        self.configure_environment()
        self.configure_logging()
        self.results = []
        
    def configure_environment(self):
        """Configura diretórios e variáveis de ambiente"""
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        current_date = datetime.now().strftime("%Y_%m_%d")
        current_time = datetime.now().strftime("%H%M%S")
        self.COLLECTION_DIR = f"{self.BASE_DIR}/coleta_{current_date}_{current_time}"
        os.makedirs(f"{self.COLLECTION_DIR}/prints", exist_ok=True)

    def configure_logging(self):
        """Configura sistema de logging"""
        logging.getLogger("WDM").setLevel(logging.WARNING)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )

        file_handler = logging.FileHandler(
            filename=f"{self.COLLECTION_DIR}/tecnocubo.log",
            mode='a',
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def start_requests(self):
        """Inicia as requisições para as URLs alvo"""
        self.urls = [
            {
                'URL': 'https://www.tecnocubo.com.br/impressoras/bambu-lab/impressora-3d-bambu-lab-x1-carbon-combo',
                'NR_SEQ_INSINF': '1',
            }
        ]
        
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=options)
        
        self.logger.info("==== Iniciando coleta ====")
        for item in self.urls:
            self.parse_product(item)

    def close_popups(self):
        """Fecha pop-ups indesejados"""
        popups = [
            "//button[contains(@class, 'close')]",
            "//div[@id='newsletter']//button",
            "//div[contains(@class, 'cookie')]",
            ".vue-modal-close"
        ]
        for selector in popups:
            try:
                if selector.startswith(('//', './', '/')):
                    WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))).click()  # MODIFICAÇÃO: indentação corrigida
                else:
                    WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()  # MODIFICAÇÃO: indentação corrigida
                self.logger.debug(f"Pop-up fechado: {selector}")
                time.sleep(1)
            except:
                continue

    def add_to_cart(self, nr_seq_insinf):
        """Adiciona produto ao carrinho"""
        try:
            self.logger.debug("🔍 Procurando botão de compra...")
            btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "button-buy")))  # MODIFICAÇÃO: parênteses alinhados
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)  # MODIFICAÇÃO: indentação corrigida
            time.sleep(1)

            for _ in range(10):
                if not btn.get_attribute("disabled"):
                    break
                self.logger.debug("⏳ Botão ainda desabilitado, aguardando...")
                time.sleep(1)
            else:
                self.logger.warning("⚠️ Botão permaneceu desativado após espera. Forçando via JavaScript.")
                self.driver.execute_script("arguments[0].removeAttribute('disabled')", btn)
                time.sleep(0.5)

            self.driver.execute_script("arguments[0].click();", btn)
            self.logger.info("✅ Produto adicionado ao carrinho")
            time.sleep(2)

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, 
                "//div[contains(@class, 'cart') and contains(., 'Meu Carrinho')]"))  # MODIFICAÇÃO: indentação corrigida
            )
            self.driver.save_screenshot(
                f"{self.COLLECTION_DIR}/prints/modal_carrinho_{nr_seq_insinf}.png")
            self.logger.info("🖼️ Print do modal do carrinho salva com sucesso")

            return True

        except Exception as e:
            self.logger.error("❌ Erro ao adicionar ao carrinho", exc_info=False)
            self.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
            return False

    def navigate_cart(self, nr_seq_insinf):
        """Navega para o carrinho e realiza operações"""
        try:
            url_carrinho = "https://www.tecnocubo.com.br/checkout/cart"
            self.driver.get(url_carrinho)
            self.logger.debug(f"Navegando para o carrinho: {url_carrinho}")
            time.sleep(3)

            produto_no_carrinho = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.cart-item")))
            
            produto_no_carrinho.screenshot(
                f"{self.COLLECTION_DIR}/prints/carrinho_{nr_seq_insinf}.png")
            self.logger.debug("Print do carrinho salva")
            
            self.close_popups()
            
        except Exception as e:
            self.logger.error("❌ Falha ao navegar para o carrinho", exc_info=False)
            self.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

    def parse_product(self, item):
        """Extrai dados do produto"""
        try:
            self.logger.info(f"Coletando produto: {item['URL']}")
            time.sleep(random.uniform(1, 3))
            self.driver.get(item['URL'])
            time.sleep(random.uniform(2, 4))

            self.close_popups()
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3)")
            time.sleep(1)
            ActionChains(self.driver).move_by_offset(10, 10).perform()
            self.driver.execute_script("window.scrollBy(0, 300)")
            time.sleep(random.uniform(1, 2))
            self.close_popups()
            time.sleep(1)

            try:
                nome_produto = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-name"))
                ).text

                todos_precos = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'R$')]")
                preco_desconto = next(
                    (preco.text for preco in todos_precos if 'à vista' in preco.text),
                    "N/A"
                )

                try:
                    preco_original = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), 'de R$')]").text.split("de ")[-1]
                except:
                    self.logger.warning("⚠️ Preço original não encontrado. Produto pode não ter desconto.")
                    preco_original = "N/A"

                disponibilidade = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, 
                    "//*[contains(text(), 'Disponibilidade:')]"))
                ).text.split(":")[-1].strip()

                self.results.append({
                    'URL': item['URL'],
                    'NR_SEQ_INSINF': item['NR_SEQ_INSINF'],
                    'nome_produto': nome_produto,
                    'preco_original': preco_original,
                    'preco_desconto': preco_desconto,
                    'disponibilidade': disponibilidade,
                    'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                if self.add_to_cart(item['NR_SEQ_INSINF']):
                    self.navigate_cart(item['NR_SEQ_INSINF'])

            except Exception as e:
                self.logger.error("Erro na coleta", exc_info=False)
                self.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
                with open(f"{self.COLLECTION_DIR}/prints/html_debug_{item['NR_SEQ_INSINF']}.html", 
                         "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)

        except Exception as e:
            self.logger.error("Erro no processamento", exc_info=False)
            self.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

    def save_results(self):
        """Salva os resultados coletados"""
        try:
            if self.results:
                import openpyxl
                df = pd.DataFrame(self.results)
                df.to_excel(f"{self.COLLECTION_DIR}/carga_saida.xlsx", 
                           index=False, engine='openpyxl')
                self.logger.info(f"✅ {len(self.results)} item(ns) coletado(s) com sucesso")
            else:
                self.logger.warning("⚠️ Nenhum item foi coletado")
        except ImportError:
            self.logger.critical("❌ Biblioteca openpyxl não instalada. Instale com 'pip install openpyxl' para salvar Excel.")
        except Exception as e:
            self.logger.error("❌ Erro ao salvar Excel", exc_info=False)
            self.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

    def close_spider(self):
        """Finaliza o spider"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        self.logger.info("==== Coleta finalizada ====")

if __name__ == "__main__":
    spider = TecnoCuboSpider()
    try:
        spider.start_requests()
        spider.save_results()
    except Exception as e:
        spider.logger.critical("❌ ERRO GLOBAL", exc_info=False)
        spider.logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
    finally:
        spider.close_spider()