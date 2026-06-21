"""
Configurações da aplicação, lidas de variáveis de ambiente quando disponíveis.
Mantém valores padrão sensatos para rodar localmente sem nenhuma configuração extra.
"""
import os

# URL base da API oficial do Clash Royale
# URL base da API oficial do Clash Royale.
# Por padrão aponta pro proxy público da RoyaleAPI (https://proxy.royaleapi.dev/v1)
# em vez da API oficial (https://api.clashroyale.com/v1). Isso é necessário porque
# plataformas serverless como a Vercel não garantem um IP de saída fixo — cada
# execução pode sair por um IP diferente, o que quebra chaves da API do Clash
# Royale, que exigem IP fixo autorizado. O proxy da RoyaleAPI já tem seu próprio
# IP fixo (45.79.218.79) registrado, então funciona normalmente nesses ambientes.
# Para rodar contra a API oficial direto (ex: servidor próprio com IP fixo),
# defina CR_BASE_URL=https://api.clashroyale.com/v1 nas variáveis de ambiente.
CR_BASE_URL = os.environ.get("CR_BASE_URL", "https://proxy.royaleapi.dev/v1")

# Timeout (segundos) para cada chamada HTTP à API da Supercell
CR_TIMEOUT = float(os.environ.get("CR_TIMEOUT", "10"))

# Tentativas automáticas em caso de erro transitório (5xx, timeout, conexão)
CR_MAX_RETRIES = int(os.environ.get("CR_MAX_RETRIES", "2"))

# TTL do cache em memória, em segundos. 0 desativa o cache.
# Útil sobretudo em execução local / servidor com processo persistente;
# em ambientes serverless (Vercel) o cache só sobrevive enquanto a instância
# estiver "quente", então trate como otimização best-effort, não garantia.
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "60"))

# Debug do Flask. Por padrão DESLIGADO — nunca deve ir True em produção
# (expõe o debugger interativo do Werkzeug, que permite execução de código).
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))

# Charset válido de tags do Clash Royale/Clash of Clans (Base32 customizado da Supercell)
VALID_TAG_CHARS = "0289PYLQGRJCUV"
