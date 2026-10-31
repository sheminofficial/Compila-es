# Falelo Originals — Inworld TTS-2

Contém os dez roteiros com direção vocal em inglês entre colchetes, 161 falas individuais em `falas.json`, e um mapa editável de 25 personagens em `vozes.json`. O texto falado está em `spokenText`; o campo `text` acrescenta a direção vocal antes dele. Use `inworld-tts-2`: Flash ignora essas instruções. As 161 falas permanecem separadas, inclusive versões por nível e desfechos alternativos.

## Antes de gerar

1. Entre em https://platform.inworld.ai/ e abra **Manage → API Keys → Generate new key → Standard → Generate**. Copie **Basic (Base64)**, exatamente como apresentado. Não publique a chave no repositório, neste arquivo ou na conversa.
2. No repositório GitHub, abra **Settings → Secrets and variables → Actions → New repository secret**. Nome: `INWORLD_API_KEY`; valor: a credencial **Basic (Base64)**, sem escrever `Basic ` antes. O workflow já acrescenta esse prefixo na requisição.
3. O programa consulta as vozes de sistema inglesas disponíveis e escolhe um ID consistente para cada um dos 25 personagens, preferindo a categoria vocal apropriada quando fornecida no catálogo. A escolha fica salva em `vozes-escolhidas.json`. Para fixar uma voz manualmente, escreva o ID em `vozes.json`; campos vazios recebem seleção automática. Escute os áudios antes de integrá-los ao aplicativo.
4. Copie `falas.json`, `vozes.json` e `inworld_batch.py` para a raiz do repositório; copie `falelo-inworld.yml` para `.github/workflows/falelo-inworld.yml`. Pode manter `roteiros/` para consulta. Execute **Actions → Falelo Inworld batch → Run workflow**.

## Uso pelo GitHub Actions

- `generate`: consulta o catálogo, escolhe as vozes, submete os cinco lotes sequencialmente e baixa os MP3. A execução pode levar horas; o Actions limita o tempo do job. A lista das operações aceitas é salva a cada submissão para recuperação.
- `validate`: confere contagem e tamanho dos lotes sem chamar Inworld. Não exige chave.
- `submit`: escolha `batch_number` de 1 a 5 (confira a saída de `validate`). Anote a linha `operation` do log. Submeta cada lote uma vez; não repita um lote aceito, para não gerar cobrança duplicada.
- `collect`: cole o nome completo da operação em `operation_name`. Se ainda estiver rodando, execute `collect` novamente mais tarde. Quando terminar, baixe o artifact `falelo-audios`, que contém um MP3 por cue e `falhas.json`.

O limite On-Demand documentado é de 10.000 caracteres de texto por batch. Este pacote divide cerca de 35.547 caracteres (incluindo direção vocal) em lotes de até 8.000. São aproximadamente cinco lotes, gerados independentemente; a API Batch pode levar horas. Os links de resultado expiram aproximadamente sete dias após a conclusão. Confira `falhas.json` de cada lote e o áudio de cada personagem antes de integrar ao Falelo. O serviço não garante 0,3 s de silêncio nas pontas.

## Uso local alternativo

Com Python 3, defina `INWORLD_API_KEY` como variável de ambiente privada e execute `python inworld_batch.py validate`, `python inworld_batch.py submit --batch 1` e `python inworld_batch.py collect --operation 'workspaces/.../operations/...'`. Não armazene a chave em arquivos ou comandos versionados.
