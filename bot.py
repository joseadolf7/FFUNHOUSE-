import asyncio
import json
import time
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '8148752386:AAHxFtIBSiakFG6TKgJEDgDi6yYTZHpRQ54'
ADMINS = [6472213397]
EXECUTIVOS = [7768324356]

ARQUIVO_DADOS = "dados.json"

# Dados em memória
usuarios = {}
duelos = {}
personal_nomes = {}
boost_lucky = {}
chance_mine = 50
cooldowns = {}

# --- Funções para salvar/carregar dados ---

def salvar_dados():
    dados = {
        "usuarios": usuarios,
        "duelos": duelos,
        "personal_nomes": personal_nomes,
        "boost_lucky": boost_lucky,
        "chance_mine": chance_mine
    }
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump(dados, f)

def carregar_dados():
    global usuarios, duelos, personal_nomes, boost_lucky, chance_mine
    try:
        with open(ARQUIVO_DADOS, "r") as f:
            dados = json.load(f)
            usuarios = dados.get("usuarios", {})
            duelos = dados.get("duelos", {})
            personal_nomes = dados.get("personal_nomes", {})
            boost_lucky = {int(k):v for k,v in dados.get("boost_lucky", {}).items()}
            chance_mine = dados.get("chance_mine", 50)
    except FileNotFoundError:
        # Arquivo não existe ainda, iniciar vazio
        usuarios = {}
        duelos = {}
        personal_nomes = {}
        boost_lucky = {}
        chance_mine = 50

# --- Utilitários ---

def anti_spam(user_id, segundos=5):
    agora = time.time()
    if user_id in cooldowns and agora - cooldowns[user_id] < segundos:
        return False
    cooldowns[user_id] = agora
    return True

def get_user(user_id):
    user_id = str(user_id)
    if user_id not in usuarios:
        usuarios[user_id] = {'saldo': 100, 'vitorias': 0, 'derrotas': 0}
        salvar_dados()
    return usuarios[user_id]

# --- Comandos ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text("🎰 Bem-vindo ao Cassino FFun House!")

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(f"💰 Saldo: {user['saldo']} moedas")

async def jogar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not anti_spam(update.effective_user.id):
        await update.message.reply_text("⏳ Aguarde para não spammar comandos.")
        return
    user = get_user(update.effective_user.id)
    try:
        aposta = int(context.args[0]) if context.args else 10
    except:
        await update.message.reply_text("⛔ Use: /jogar <valor>")
        return
    if aposta <= 0 or aposta > user['saldo']:
        await update.message.reply_text("⛔ Aposta inválida.")
        return
    ganhou = random.randint(1, 100) <= 50
    if ganhou:
        user['saldo'] += aposta
        user['vitorias'] += 1
        await update.message.reply_text(f"🎉 Você ganhou {aposta} moedas!")
    else:
        user['saldo'] -= aposta
        user['derrotas'] += 1
        await update.message.reply_text(f"💸 Você perdeu {aposta} moedas.")
    salvar_dados()

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not anti_spam(update.effective_user.id):
        await update.message.reply_text("⏳ Aguarde para não spammar comandos.")
        return
    user = get_user(update.effective_user.id)
    try:
        aposta = int(context.args[0]) if context.args else 10
    except:
        await update.message.reply_text("⛔ Use: /mine <valor>")
        return
    if aposta <= 0 or aposta > user['saldo']:
        await update.message.reply_text("⛔ Aposta inválida.")
        return
    chance = chance_mine
    if update.effective_user.id in boost_lucky:
        if time.time() - boost_lucky[update.effective_user.id] < 300:
            chance += 20
    ganhou = random.randint(1, 100) <= chance
    if ganhou:
        user['saldo'] += aposta
        user['vitorias'] += 1
        await update.message.reply_text(f"💎 Você achou um prêmio e ganhou {aposta} moedas!")
    else:
        user['saldo'] -= aposta
        user['derrotas'] += 1
        await update.message.reply_text("💥 Você pisou na bomba e perdeu tudo!")
    salvar_dados()

async def roleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not anti_spam(update.effective_user.id):
        await update.message.reply_text("⏳ Aguarde para não spammar comandos.")
        return
    user = get_user(update.effective_user.id)
    try:
        aposta = int(context.args[0]) if context.args else 10
    except:
        await update.message.reply_text("⛔ Use: /roleta <valor>")
        return
    if aposta <= 0 or aposta > user['saldo']:
        await update.message.reply_text("⛔ Aposta inválida.")
        return
    await update.message.reply_text("🎲 Girando a roleta...")
    await asyncio.sleep(3)
    ganhou = random.choice([True, False])
    if ganhou:
        user['saldo'] += aposta
        user['vitorias'] += 1
        await update.message.reply_text(f"🟢 Caiu verde! Você ganhou {aposta} moedas.")
    else:
        user['saldo'] -= aposta
        user['derrotas'] += 1
        await update.message.reply_text(f"🔴 Caiu vermelho! Você perdeu {aposta} moedas.")
    salvar_dados()

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = sorted(usuarios.items(), key=lambda x: x[1]['saldo'], reverse=True)[:5]
    msg = "🏆 Top 5 Jogadores:\n"
    for i, (uid, dados) in enumerate(top, 1):
        nome = personal_nomes.get(uid, f"[{uid}](tg://user?id={uid})")
        msg += f"{i}. {nome} – 💰 {dados['saldo']} moedas\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def doar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⛔ Responda a alguém para doar.")
        return
    try:
        valor = int(context.args[0])
    except:
        await update.message.reply_text("💸 Use: /doar <quantia>")
        return
    if valor <= 0:
        await update.message.reply_text("⛔ Valor inválido.")
        return
    de = get_user(update.effective_user.id)
    para_id = update.message.reply_to_message.from_user.id
    para = get_user(para_id)
    if de['saldo'] < valor:
        await update.message.reply_text("💸 Saldo insuficiente.")
        return
    de['saldo'] -= valor
    para['saldo'] += valor
    salvar_dados()
    await update.message.reply_text(f"✅ Você doou {valor} moedas para {update.message.reply_to_message.from_user.first_name}.")

async def duelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Responda a alguém para desafiar.")
        return
    try:
        valor = int(context.args[0])
    except:
        await update.message.reply_text("Use: /duelo <valor>")
        return
    desafiador = str(update.effective_user.id)
    desafiado = str(update.message.reply_to_message.from_user.id)
    if desafiador == desafiado:
        await update.message.reply_text("Você não pode duelar com você mesmo.")
        return
    duelos[desafiado] = {'contra': desafiador, 'valor': valor}
    salvar_dados()
    await update.message.reply_text(f"⚔️ Desafio enviado! {update.message.reply_to_message.from_user.first_name} use /aceitarduelo")

async def aceitarduelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in duelos:
        await update.message.reply_text("Você não tem nenhum duelo pendente.")
        return
    duelo_info = duelos.pop(user_id)
    desafiante = duelo_info['contra']
    valor = duelo_info['valor']
    user1 = get_user(user_id)
    user2 = get_user(desafiante)
    if user1['saldo'] < valor or user2['saldo'] < valor:
        await update.message.reply_text("Um dos jogadores não tem saldo suficiente.")
        return
    vencedor = random.choice([user_id, desafiante])
    perdedor = desafiante if vencedor == user_id else user_id
    get_user(vencedor)['saldo'] += valor
    get_user(perdedor)['saldo'] -= valor
    salvar_dados()
    await update.message.reply_text(f"🏆 Vencedor: [{vencedor}](tg://user?id={vencedor})", parse_mode="Markdown")

async def roubar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Responda a alguém para tentar roubar.")
        return
    alvo_id = str(update.message.reply_to_message.from_user.id)
    ladrao_id = str(update.effective_user.id)
    if random.randint(1, 100) <= 50:
        valor = random.randint(5, 20)
        alvo = get_user(alvo_id)
        ladrao = get_user(ladrao_id)
        if alvo['saldo'] >= valor:
            alvo['saldo'] -= valor
            ladrao['saldo'] += valor
            salvar_dados()
            await update.message.reply_text(f"🕵️‍♂️ Você roubou {valor} moedas!")
        else:
            await update.message.reply_text("Alvo sem saldo suficiente.")
    else:
        await update.message.reply_text("🚨 Você foi pego!")

async def dar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    if not update.message.reply_to_message:
        return
    try:
        valor = int(context.args[0])
        alvo_id = str(update.message.reply_to_message.from_user.id)
        get_user(alvo_id)['saldo'] += valor
        salvar_dados()
        await update.message.reply_text(f"✅ {valor} moedas adicionadas.")
    except:
        await update.message.reply_text("Uso: /dar <valor>")

async def resetar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    if not update.message.reply_to_message:
        return
    alvo_id = str(update.message.reply_to_message.from_user.id)
    usuarios[alvo_id] = {'saldo': 100, 'vitorias': 0, 'derrotas': 0}
    salvar_dados()
    await update.message.reply_text("♻️ Jogador resetado.")

async def limparranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    usuarios.clear()
    salvar_dados()
    await update.message.reply_text("📉 Ranking limpo.")

async def setchance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    global chance_mine
    try:
        chance = int(context.args[0])
        if 0 < chance <= 100:
            chance_mine = chance
            salvar_dados()
            await update.message.reply_text(f"🔧 Chance do /mine alterada para {chance}%")
    except:
        await update.message.reply_text("Uso: /setchance <1 a 100>")

async def lucky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in EXECUTIVOS:
        return
    boost_lucky[update.effective_user.id] = time.time()
    salvar_dados()
    await update.message.reply_text("🍀 Chance aumentada por 5 minutos!")

async def personalinome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in EXECUTIVOS:
        return
    nome = " ".join(context.args)
    if not nome:
        await update.message.reply_text("Digite o nome após o comando.")
        return
    personal_nomes[str(update.effective_user.id)] = nome
    salvar_dados()
    await update.message.reply_text(f"✅ Nome personalizado definido: {nome}")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in EXECUTIVOS:
        return
    total = sum(u['saldo'] for u in usuarios.values())
    await update.message.reply_text(f"📊 Total de moedas no sistema: {total}")

# --- MAIN ---

async def main():
    carregar_dados()
    app = ApplicationBuilder().token(TOKEN).build()

    comandos = [
        ("start", start), ("saldo", saldo), ("jogar", jogar), ("mine", mine), ("roleta", roleta),
        ("ranking", ranking), ("doar", doar), ("duelo", duelo), ("aceitarduelo", aceitarduelo), ("roubar", roubar),
        ("dar", dar), ("resetar", resetar), ("limparranking", limparranking), ("setchance", setchance),
        ("lucky", lucky), ("personalinome", personalinome), ("relatorio", relatorio)
    ]

    for nome, func in comandos:
        app.add_handler(CommandHandler(nome, func))

    print("🎰 Bot Cassino ONLINE!")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
