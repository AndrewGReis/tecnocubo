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

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
current_date = datetime.now().strftime("%Y_%m_%d")
current_time = datetime.now().strftime("%H%M%S")
COLLECTION_DIR = f"{BASE_DIR}/coleta_{current_date}_{current_time}"

os.makedirs(f"{COLLECTION_DIR}/prints", exist_ok=True)

logging.getLogger("WDM").setLevel(logging.WARNING)

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )

    file_handler = logging.FileHandler(
        filename=f"{COLLECTION_DIR}/tecnocubo.log",
        mode='a',
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

configure_logging()
logger = logging.getLogger(__name__)

urls = [
    {
        'URL': 'https://www.tecnocubo.com.br/impressoras/bambu-lab/impressora-3d-bambu-lab-x1-carbon-combo',
        'NR_SEQ_INSINF': '1',
    }
]

def fechar_popups(driver):
    popups = [
        "//button[contains(@class, 'close')]",
        "//div[@id='newsletter']//button",
        "//div[contains(@class, 'cookie')]",
        ".vue-modal-close"
    ]
    for selector in popups:
        try:
            if selector.startswith(('//', './', '/')):
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, selector))).click()
            else:
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()
            logger.debug(f"Pop-up fechado: {selector}")
            time.sleep(1)
        except:
            continue

def adicionar_ao_carrinho(driver, nr_seq_insinf):
    try:
        logger.debug("🔍 Procurando botão de compra...")
        btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "button-buy"))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(1)

        for _ in range(10):
            if not btn.get_attribute("disabled"):
                break
            logger.debug("⏳ Botão ainda desabilitado, aguardando...")
            time.sleep(1)
        else:
            logger.warning("⚠️ Botão permaneceu desativado após espera. Forçando via JavaScript.")
            driver.execute_script("arguments[0].removeAttribute('disabled')", btn)
            time.sleep(0.5)

        driver.execute_script("arguments[0].click();", btn)
        logger.info("✅ Produto adicionado ao carrinho")
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'cart') and contains(., 'Meu Carrinho')]"))
        )
        driver.save_screenshot(f"{COLLECTION_DIR}/prints/modal_carrinho_{nr_seq_insinf}.png")
        logger.info("🖼️ Print do modal do carrinho salva com sucesso")

        return True

    except Exception as e:
        logger.error("❌ Erro ao adicionar ao carrinho", exc_info=False)
        logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
        return False

def navegar_para_carrinho(driver, nr_seq_insinf):
    try:
        url_carrinho = "https://www.tecnocubo.com.br/checkout/cart"
        driver.get(url_carrinho)
        logger.debug(f"Navegando para o carrinho: {url_carrinho}")
        time.sleep(5)

        produto_no_carrinho = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.cart-item"))
        )
        produto_no_carrinho.screenshot(f"{COLLECTION_DIR}/prints/carrinho_{nr_seq_insinf}.png")
        logger.debug("Print do carrinho salva")
    except Exception as e:
        logger.error("❌ Falha ao navegar para o carrinho", exc_info=False)
        logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

try:
    logger.info("==== Iniciando coleta ====")

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#/\ essa linha pode ser substituída por essa     driver = webdriver.Chrome(options=options)
# sem prejuízo ao código
    resultados = []

    for item in urls:
        try:
            logger.info(f"Coletando produto: {item['URL']}")
            time.sleep(random.uniform(1, 3))
            driver.get(item['URL'])
            time.sleep(random.uniform(2, 4))

            fechar_popups(driver)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3)")
            time.sleep(1)
            ActionChains(driver).move_by_offset(10, 10).perform()
            driver.execute_script("window.scrollBy(0, 300)")
            time.sleep(random.uniform(1, 2))
            fechar_popups(driver)
            time.sleep(1)

            try:
                nome_produto = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-name"))
                ).text

                todos_precos = driver.find_elements(By.XPATH, "//*[contains(text(), 'R$')]")
                preco_desconto = next(
                    (preco.text for preco in todos_precos if 'à vista' in preco.text),
                    "N/A"
                )

                try:
                    preco_original = driver.find_element(By.XPATH, "//*[contains(text(), 'de R$')]").text.split("de ")[-1]
                except:
                    logger.warning("⚠️ Preço original não encontrado. Produto pode não ter desconto.")
                    preco_original = "N/A"

                disponibilidade = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Disponibilidade:')]"))
                ).text.split(":")[-1].strip()

                resultados.append({
                    'URL': item['URL'],
                    'NR_SEQ_INSINF': item['NR_SEQ_INSINF'],
                    'nome_produto': nome_produto,
                    'preco_original': preco_original,
                    'preco_desconto': preco_desconto,
                    'disponibilidade': disponibilidade,
                    'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                if adicionar_ao_carrinho(driver, item['NR_SEQ_INSINF']):
                    navegar_para_carrinho(driver, item['NR_SEQ_INSINF'])

            except Exception as e:
                logger.error("Erro na coleta", exc_info=False)
                logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
                with open(f"{COLLECTION_DIR}/prints/html_debug_{item['NR_SEQ_INSINF']}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                continue

        except Exception as e:
            logger.error("Erro no processamento", exc_info=False)
            logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)
            continue

    try:
        if resultados:
            import openpyxl
            df = pd.DataFrame(resultados)
            df.to_excel(f"{COLLECTION_DIR}/carga_saida.xlsx", index=False, engine='openpyxl')
            logger.info(f"✅ {len(resultados)} item(ns) coletado(s) com sucesso")
        else:
            logger.warning("⚠️ Nenhum item foi coletado")
    except ImportError:
        logger.critical("❌ Biblioteca openpyxl não instalada. Instale com 'pip install openpyxl' para salvar Excel.")
    except Exception as e:
        logger.error("❌ Erro ao salvar Excel", exc_info=False)
        logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

except Exception as e:
    logger.critical("❌ ERRO GLOBAL", exc_info=False)
    logger.debug(f"Detalhes técnicos: {str(e)}", exc_info=True)

finally:
    if 'driver' in locals():
        driver.quit()
    logger.info("==== Coleta finalizada ====")
