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

# Configurações iniciais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
current_date = datetime.now().strftime("%Y_%m_%d")
current_time = datetime.now().strftime("%H%M%S")
COLLECTION_DIR = f"{BASE_DIR}/coleta_{current_date}_{current_time}"

os.makedirs(f"{COLLECTION_DIR}/prints", exist_ok=True)

# Configuração de logging
def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
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

# Lista de URLs
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

# ✅ FUNÇÃO MODIFICADA: Usa o botão real com id="button-buy"
def adicionar_ao_carrinho(driver):
    try:
        btn_carrinho = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#button-buy"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_carrinho)
        time.sleep(1)
        ActionChains(driver).move_to_element(btn_carrinho).perform()
        time.sleep(0.5)
        btn_carrinho.click()
        logger.info("✅ Produto adicionado ao carrinho com sucesso")
        time.sleep(3)
        return True
    except Exception as e:
        logger.error(f"❌ Falha ao adicionar ao carrinho: {str(e)}")
        return False

# Execução principal
try:
    logger.info("==== Coleta iniciada ====")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    resultados = []
    
    for item in urls:
        try:
            logger.debug(f"Processando item {item['NR_SEQ_INSINF']}: {item['URL']}")
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

                # ✅ MODIFICAÇÃO: Captura o elemento que contém o preço
                todos_precos = driver.find_elements(By.XPATH, "//*[contains(text(), 'R$')]")
                preco_desconto = next(
                    (preco.text for preco in todos_precos if 'à vista' in preco.text), 
                    "N/A"
                )

                preco_original = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'de R$')]"))
                ).text.split("de ")[-1]

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
                
                driver.save_screenshot(f"{COLLECTION_DIR}/prints/{item['NR_SEQ_INSINF']}.png")
                logger.debug(f"Coletado: {nome_produto} | De: {preco_original} | Por: {preco_desconto}")
                
                adicionar_ao_carrinho(driver)
                
            except Exception as e:
                logger.error(f"Erro na coleta: {str(e)}")
                # ✅ Extra: salvar HTML da página para debugar depois
                with open(f"{COLLECTION_DIR}/prints/html_debug_{item['NR_SEQ_INSINF']}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                continue
    
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            continue
    
    if resultados:
        df = pd.DataFrame(resultados)
        df.to_excel(f"{COLLECTION_DIR}/carga_saida.xlsx", index=False, engine='openpyxl')
        logger.info(f"✅ {len(resultados)} itens coletados com sucesso")
    else:
        logger.warning("⚠️ Nenhum item foi coletado")

except Exception as e:
    logger.critical(f"❌ ERRO GLOBAL: {str(e)}")
finally:
    if 'driver' in locals():
        driver.quit()
    logger.info("==== Coleta finalizada ====")
