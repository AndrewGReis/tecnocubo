import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# Configurações iniciais
BASE_DIR = "C:/Users/andrew.reis/Documents/projetos/Web/TECNOCUBO"
current_date = datetime.now().strftime("%Y_%m_%d")
current_time = datetime.now().strftime("%H%M%S")
COLLECTION_DIR = f"{BASE_DIR}/coleta_2025/coleta_maio/coleta_2_dec/coleta_{current_date}_{current_time}"

# Criar estrutura de pastas
os.makedirs(f"{COLLECTION_DIR}/prints", exist_ok=True)

# Configuração avançada de logging (MODIFICADO)
def configure_logging():
    """Configura sistema duplo de logs (terminal simplificado + arquivo detalhado)"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formato para arquivo (detalhado)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(
        filename=f"{COLLECTION_DIR}/tecnocubo.log",
        mode='a',
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para terminal (simplificado)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Inicializa logging
configure_logging()
logger = logging.getLogger(__name__)

# Lista de URLs para processar
urls = [
    {
        'URL': 'https://www.tecnocubo.com.br/filamento-impressao-3d-creality-hyper-pla-rainbow-arco-iris-spring-lake-1kg/p',
        'NR_SEQ_INSINF': '1',
    }
]

# Inicializar o navegador
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
            
            driver.get(item['URL'])
            
            # Fechar pop-up
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'close')]"))
                ).click()
                logger.debug("Pop-up fechado")
            except:
                pass
            
            # Coleta de dados
            try:
                nome_produto = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[@class='product-name']"))
                ).text
                
                preco_produto = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='price-sales']"))
                ).text
                
                resultados.append({
                    'URL': item['URL'],
                    'NR_SEQ_INSINF': item['NR_SEQ_INSINF'],
                    'nome_produto': nome_produto,
                    'preco_coleta': preco_produto,
                    'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Screenshot
                driver.save_screenshot(f"{COLLECTION_DIR}/prints/{item['NR_SEQ_INSINF']}.png")
                logger.debug(f"Coletado: {nome_produto} - {preco_produto}")
                
            except Exception as e:
                logger.error(f"Erro na coleta: {str(e)}")
                continue
    
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            continue
    
    # Resultado final
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