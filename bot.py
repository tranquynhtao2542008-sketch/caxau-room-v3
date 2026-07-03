# ============================================
# 🐊 CÁ XẤU ROOM v3 - GIAO DIỆN TUYỆT ĐẸP & NHIỀU GAME
# ============================================
import random, json, os, logging, threading, time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚙️ TOKEN & ADMIN ID (đã điền sẵn của bạn)
ADMIN_TOKEN = "8805149476:AAGmqFVvyMUKW48mFvHkqQd6hRxlUWnm-wk"
ROOM_TOKEN = "7945714508:AAGeBzVYjLJjlSM7E2K0QA73i2FuPL6ToyM"
PROFILE_TOKEN = "8888675958:AAHkxzqCmKhI07tiPJIUjc5C2cQcnxexQwo"
ADMIN_IDS = ["8823176709"]

# 📁 File lưu trữ
DATA_FILE = "caxau_v3_data.json"
ROOMS_FILE = "caxau_v3_rooms.json"
PENDING_FILE = "pending.json"

# ========== DATABASE ==========
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class DB:
    def __init__(self):
        self.players = load_json(DATA_FILE)
        self.rooms = load_json(ROOMS_FILE) or {
            "main": {"id":"main","name":"Phòng Chính","creator":"system","members":[],"settings":{"bet":10000,"duration":30}}
        }
        self.pending = load_json(PENDING_FILE)

    def save(self):
        save_json(self.players, DATA_FILE)
        save_json(self.rooms, ROOMS_FILE)
        save_json(self.pending, PENDING_FILE)

db = DB()

def get_player(uid):
    if uid not in db.players:
        db.players[uid] = {
            "balance":10000,"username":"","total_deposit":0,"daily_bet":0,
            "vip":0,"last_daily":"","wins":0,"losses":0
        }
        db.save()
    return db.players[uid]

# ========== TIỆN ÍCH GIAO DIỆN ==========
def table(headers, rows, title=None):
    t = f"<b>{title}</b>\n" if title else ""
    t += "<pre>"
    t += "┌" + "┬".join(["─"*(len(h)+2) for h in headers]) + "┐\n"
    t += "│" + "│".join([f" {h} " for h in headers]) + "│\n"
    t += "├" + "┼".join(["─"*(len(h)+2) for h in headers]) + "┤\n"
    for row in rows:
        cells = [f" {str(c).ljust(len(headers[i]))} " for i,c in enumerate(row)]
        t += "│" + "│".join(cells) + "│\n"
    t += "└" + "┴".join(["─"*(len(h)+2) for h in headers]) + "┘"
    t += "</pre>"
    return t

def emoji_dice(d):
    return ['⚀','⚁','⚂','⚃','⚄','⚅'][d-1]

def emoji_bc(v):
    return ['🫙','🦀','🦐','🐟','🐔','🦌'][v]

# ========== GAME ENGINE ==========
class Games:
    @staticmethod
    def taixiu():
        d = [random.randint(1,6) for _ in range(3)]
        total = sum(d)
        return d, total, total>=11

    @staticmethod
    def chanle():
        d = [random.randint(1,6) for _ in range(3)]
        total = sum(d)
        return d, total, total%2==0

    @staticmethod
    def bau_cua():
        return [random.randint(0,5) for _ in range(3)]

    @staticmethod
    def xoc_dia():
        return [random.choice(['sấp','ngửa']) for _ in range(4)]

    @staticmethod
    def slot():
        symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣']
        return [random.choice(symbols) for _ in range(3)]

    @staticmethod
    def kbb(player):
        bot = random.choice(['kéo','búa','bao'])
        if player==bot: return bot, 'draw'
        win = {'kéo':'bao','búa':'kéo','bao':'búa'}
        return bot, 'win' if win[player]==bot else 'lose'

# ========== ADMIN BOT ==========
class AdminBot:
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_user.id) not in ADMIN_IDS: return
        total_players = len(db.players)
        total_balance = sum(p.get('balance',0) for p in db.players.values())
        text = table(["📊 CHỈ SỐ","GIÁ TRỊ"],
            [["👥 Người chơi",total_players],["💰 Tổng dư",f"{total_balance:,}đ"],
             ["🏠 Phòng",len(db.rooms)],["⏳ Chờ",len(db.pending)]],
            "🐊 CÁ XẤU ADMIN")
        await update.message.reply_text(text, reply_markup=self.menu(), parse_mode='HTML')

    def menu(self):
        kb = [[InlineKeyboardButton("👥 DS người chơi", callback_data="ad_players"),
               InlineKeyboardButton("💰 Duyệt GD", callback_data="ad_pending")],
              [InlineKeyboardButton("🎁 Tạo giftcode", callback_data="ad_gift"),
               InlineKeyboardButton("🏠 Quản lý phòng", callback_data="ad_rooms")]]
        return InlineKeyboardMarkup(kb)

    async def button(self, update, context):
        q = update.callback_query; await q.answer()
        if str(update.effective_user.id) not in ADMIN_IDS: return
        d = q.data
        if d == "ad_players":
            rows = [[uid, p.get('username','?'), f"{p.get('balance',0):,}đ", f"VIP{p.get('vip',0)}"] for uid,p in list(db.players.items())[:10]]
            await q.edit_message_text(table(["ID","User","Số dư","VIP"], rows, "👥 Người chơi"), reply_markup=self.menu(), parse_mode='HTML')
        elif d == "ad_pending":
            if not db.pending: await q.edit_message_text("✅ Không có GD chờ.", reply_markup=self.menu())
            else:
                for tid, t in list(db.pending.items())[:5]:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"app_{tid}"), InlineKeyboardButton("❌ Từ chối", callback_data=f"rej_{tid}")]])
                    await context.bot.send_message(update.effective_chat.id, f"🔑 {tid}\n👤 {t['user_id']}\n💰 {t['amount']:,}đ", reply_markup=kb)
        elif d.startswith("app_"):
            tid = d[4:]; trans = db.pending.pop(tid,None)
            if trans:
                uid = trans['user_id']; p = get_player(uid)
                p['balance'] += trans['amount']; p['total_deposit'] += trans['amount']
                db.save()
                await q.edit_message_text(f"✅ Đã duyệt {trans['amount']:,}đ cho {uid}")
        elif d.startswith("rej_"):
            db.pending.pop(d[4:],None); db.save()
            await q.edit_message_text("❌ Đã từ chối.")

    def run(self):
        app = Application.builder().token(ADMIN_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.button))
        app.run_polling()

# ========== ROOM BOT (ĐA PHÒNG, GAME ĐA DẠNG) ==========
class RoomBot:
    def __init__(self):
        self.active = {}

    async def start(self, update, context):
        uid = str(update.effective_user.id)
        my_rooms = [r for r in db.rooms.values() if uid in r['members']]
        if not my_rooms:
            db.rooms["main"]['members'].append(uid); db.save()
            my_rooms = [db.rooms["main"]]
        kb = [[InlineKeyboardButton(f"🏠 {r['name']}", callback_data=f"enter_{r['id']}")] for r in my_rooms]
        kb.append([InlineKeyboardButton("➕ Tạo phòng", callback_data="create_room")])
        await update.message.reply_text("🐊 <b>CÁ XẤU ROOM</b> - Chọn phòng:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    async def button(self, update, context):
        q = update.callback_query; await q.answer()
        uid = str(update.effective_user.id); d = q.data
        if d.startswith("enter_"):
            rid = d[6:]
            room = db.rooms.get(rid)
            if not room: return
            if uid not in room['members']:
                room['members'].append(uid); db.save()
            await self.lobby(update, context, rid)
        elif d.startswith("play_"):
            _, game, rid = d.split('_',2)
            await self.start_game(update, context, rid, game)
        elif d.startswith("bet_"):
            await self.resolve_bet(update, context)

    async def lobby(self, update, context, rid):
        room = db.rooms.get(rid)
        if not room: return
        games = [
            [InlineKeyboardButton("🎲 Tài Xỉu", callback_data=f"play_taixiu_{rid}"),
             InlineKeyboardButton("🎯 Chẵn Lẻ", callback_data=f"play_chanle_{rid}")],
            [InlineKeyboardButton("🦀 Bầu Cua", callback_data=f"play_baucua_{rid}"),
             InlineKeyboardButton("🥢 Xóc Đĩa", callback_data=f"play_xocdia_{rid}")],
            [InlineKeyboardButton("🎰 Slot", callback_data=f"play_slot_{rid}"),
             InlineKeyboardButton("✊ Kéo Búa Bao", callback_data=f"play_kbb_{rid}")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="start_room")],
        ]
        bet = room['settings']['bet']
        text = f"🏠 <b>{room['name']}</b>\n👥 {len(room['members'])} thành viên\n💰 Mức cược: {bet:,}đ"
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(games), parse_mode='HTML')

    async def start_game(self, update, context, rid, game):
        room = db.rooms.get(rid)
        if not room: return
        bet = room['settings']['bet']
        if game in ('taixiu','chanle','baucua','xocdia'):
            sid = f"{rid}_{game}"
            self.active[sid] = {'bets':[], 'bet':bet, 'room':rid, 'game':game}
            if game=='taixiu':
                kb = [[InlineKeyboardButton("TÀI", callback_data=f"bet_tx_T_{sid}"),
                       InlineKeyboardButton("XỈU", callback_data=f"bet_tx_X_{sid}")]]
            elif game=='chanle':
                kb = [[InlineKeyboardButton("CHẴN", callback_data=f"bet_cl_C_{sid}"),
                       InlineKeyboardButton("LẺ", callback_data=f"bet_cl_L_{sid}")]]
            elif game=='baucua':
                faces = ['Bầu','Cua','Tôm','Cá','Gà','Nai']
                kb = [[InlineKeyboardButton(f, callback_data=f"bet_bc_{i}_{sid}") for i,f in enumerate(faces)]]
            elif game=='xocdia':
                kb = [[InlineKeyboardButton("Chẵn", callback_data=f"bet_xd_chan_{sid}"),
                       InlineKeyboardButton("Lẻ", callback_data=f"bet_xd_le_{sid}")]]
            await q.edit_message_text(
                f"🐊 <b>{game.upper()}</b> - Cược {bet:,}đ\nChọn:", 
                reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
        elif game=='slot':
            await self.play_slot(update, context, rid)
        elif game=='kbb':
            kb = [[InlineKeyboardButton(f, callback_data=f"bet_kbb_{f}_{rid}") for f in ['Kéo','Búa','Bao']]]
            await q.edit_message_text(f"✊ Kéo Búa Bao - Cược {bet:,}đ\nChọn:", 
                reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    async def resolve_bet(self, update, context):
        q = update.callback_query; await q.answer()
        uid = str(update.effective_user.id); d = q.data.split('_')
        p = get_player(uid)
        if d[0]!='bet': return
        game = d[1]
        if game in ('tx','cl','bc','xd'):
            choice = d[2]; sid = d[3]
            session = self.active.get(sid)
            if not session: await q.answer("Phiên hết hạn"); return
            if uid in [b['uid'] for b in session['bets']]: await q.answer("Đã cược"); return
            if p['balance'] < session['bet']: await q.answer("Không đủ tiền"); return
            p['balance'] -= session['bet']; p['daily_bet'] += session['bet']
            session['bets'].append({'uid':uid, 'choice':choice, 'amount':session['bet']})
            db.save()
            await q.answer(f"Đã cược {choice}")
            await q.edit_message_text(f"🐊 Cược {choice}. Chờ quay...")
            context.job_queue.run_once(self.resolve_session, 30, data={'sid':sid, 'chat':update.effective_chat.id, 'msg':q.message.message_id})
        elif game=='kbb':
            choice = d[2]; rid = d[3]
            room = db.rooms.get(rid)
            bet = room['settings']['bet'] if room else 10000
            if p['balance'] < bet: await q.answer("Không đủ tiền"); return
            p['balance'] -= bet; p['daily_bet'] += bet
            bot_choice, result = Games.kbb(choice.lower())
            if result=='win': p['balance'] += bet*2; txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Thắng +{bet*2:,}đ"
            elif result=='lose': txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Thua -{bet:,}đ"
            else: p['balance'] += bet; txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Hòa"
            db.save()
            await q.edit_message_text(f"{txt}\n💰 Số dư: <b>{p['balance']:,}đ</b>", parse_mode='HTML')

    async def resolve_session(self, context):
        job = context.job.data; sid = job['sid']; chat = job['chat']; msg = job['msg']
        session = self.active.pop(sid, None)
        if not session: return
        game = session['game']
        if game=='taixiu':
            d, total, is_tai = Games.taixiu()
            dice_str = " ".join(emoji_dice(d))
            txt = f"🎲 {dice_str} = {total} ({'TÀI' if is_tai else 'XỈU'})\n"
            for b in session['bets']:
                win = (b['choice']=='T' and is_tai) or (b['choice']=='X' and not is_tai)
                p = get_player(b['uid'])
                if win: p['balance'] += b['amount']*2; txt += f"✅ {b['uid']}: +{b['amount']*2:,}đ\n"
                else: txt += f"❌ {b['uid']}: -{b['amount']:,}đ\n"
            db.save()
        elif game=='chanle':
            d, total, is_chan = Games.chanle()
            dice_str = " ".join(emoji_dice(d))
            txt = f"🎯 {dice_str} = {total} ({'CHẴN' if is_chan else 'LẺ'})\n"
            for b in session['bets']:
                win = (b['choice']=='C' and is_chan) or (b['choice']=='L' and not is_chan)
                p = get_player(b['uid'])
                if win: p['balance'] += b['amount']*2; txt += f"✅ {b['uid']}: +{b['amount']*2:,}đ\n"
                else: txt += f"❌ {b['uid']}: -{b['amount']:,}đ\n"
            db.save()
        elif game=='baucua':
            result = Games.bau_cua()
            res_str = " ".join(emoji_bc(r) for r in result)
            txt = f"🦀 {res_str}\n"
            for b in session['bets']:
                win_count = result.count(int(b['choice']))
                if win_count:
                    win_amount = b['amount'] * (win_count+1)
                    p = get_player(b['uid']); p['balance'] += win_amount
                    txt += f"✅ {b['uid']}: +{win_amount:,}đ ({win_count} mặt)\n"
                else:
                    txt += f"❌ {b['uid']}: -{b['amount']:,}đ\n"
            db.save()
        elif game=='xocdia':
            coins = Games.xoc_dia()
            chan = coins.count('sấp')%2==0
            coin_str = " ".join(['🔵' if c=='sấp' else '🔴' for c in coins])
            txt = f"🥢 {coin_str} ({'CHẴN' if chan else 'LẺ'})\n"
            for b in session['bets']:
                win = (b['choice']=='chan' and chan) or (b['choice']=='le' and not chan)
                p = get_player(b['uid'])
                if win: p['balance'] += b['amount']*2; txt += f"✅ {b['uid']}: +{b['amount']*2:,}đ\n"
                else: txt += f"❌ {b['uid']}: -{b['amount']:,}đ\n"
            db.save()
        try: await context.bot.edit_message_text(chat_id=chat, message_id=msg, text=txt, parse_mode='HTML')
        except: pass

    async def play_slot(self, update, context, rid):
        uid = str(update.effective_user.id); p = get_player(uid)
        room = db.rooms.get(rid)
        bet = room['settings']['bet'] if room else 10000
        if p['balance'] < bet: await update.callback_query.answer("Không đủ tiền"); return
        p['balance'] -= bet; p['daily_bet'] += bet
        result = Games.slot()
        if len(set(result))==1 and result[0]=='7️⃣': win_amount = bet*10
        elif len(set(result))==1: win_amount = bet*5
        elif result[0]==result[1] or result[1]==result[2]: win_amount = bet*2
        else: win_amount = 0
        p['balance'] += win_amount
        db.save()
        txt = f"🎰 {' '.join(result)}\n"
        if win_amount: txt += f"✅ Thắng +{win_amount:,}đ"
        else: txt += f"❌ Thua -{bet:,}đ"
        txt += f"\n💰 {p['balance']:,}đ"
        await update.callback_query.edit_message_text(txt, parse_mode='HTML')

    def run(self):
        app = Application.builder().token(ROOM_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.button))
        app.run_polling()

# ========== PROFILE BOT (SHOP, NHIỆM VỤ, GAME) ==========
class ProfileBot:
    async def start(self, update, context):
        uid = str(update.effective_user.id); p = get_player(uid)
        text = f"🐊 <b>CÁ XẤU PROFILE</b>\n💰 {p['balance']:,}đ | VIP {p['vip']}\n"
        kb = [
            [InlineKeyboardButton("🎲 Tài Xỉu", callback_data="p_tx"),
             InlineKeyboardButton("🎯 Chẵn Lẻ", callback_data="p_cl")],
            [InlineKeyboardButton("🦀 Bầu Cua", callback_data="p_bc"),
             InlineKeyboardButton("🥢 Xóc Đĩa", callback_data="p_xd")],
            [InlineKeyboardButton("🎰 Slot", callback_data="p_slot"),
             InlineKeyboardButton("✊ KBB", callback_data="p_kbb")],
            [InlineKeyboardButton("🛒 Cửa hàng", callback_data="p_shop"),
             InlineKeyboardButton("💳 Nạp", callback_data="p_nap")],
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    async def button(self, update, context):
        q = update.callback_query; await q.answer()
        uid = str(update.effective_user.id); d = q.data; p = get_player(uid)
        if d in ("p_tx","p_cl","p_bc","p_xd","p_kbb","p_slot"):
            game_map = {"p_tx":"taixiu","p_cl":"chanle","p_bc":"baucua","p_xd":"xocdia","p_kbb":"kbb","p_slot":"slot"}
            game = game_map[d]
            kb = [
                [InlineKeyboardButton(f"{m}đ", callback_data=f"pbet_{game}_{m}") for m in [10000,50000,100000]],
                [InlineKeyboardButton("🔙 Quay lại", callback_data="p_menu")]
            ]
            await q.edit_message_text(f"🐊 {game.upper()} - Chọn mức cược:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
        elif d.startswith("pbet_"):
            _, game, amount = d.split('_'); amount = int(amount)
            if p['balance'] < amount: await q.answer("Không đủ tiền"); return
            if game in ("taixiu","chanle"):
                kb = [[InlineKeyboardButton("TÀI/CHẴN", callback_data=f"pbet2_{game}_T_{amount}"),
                       InlineKeyboardButton("XỈU/LẺ", callback_data=f"pbet2_{game}_X_{amount}")]]
                await q.edit_message_text(f"Cược {amount:,}đ - Chọn:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
            elif game=="baucua":
                faces = ['Bầu','Cua','Tôm','Cá','Gà','Nai']
                kb = [[InlineKeyboardButton(f, callback_data=f"pbet2_bc_{i}_{amount}") for i,f in enumerate(faces)]]
                await q.edit_message_text(f"Bầu Cua {amount:,}đ - Chọn mặt:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
            elif game=="xocdia":
                kb = [[InlineKeyboardButton("Chẵn", callback_data=f"pbet2_xd_chan_{amount}"),
                       InlineKeyboardButton("Lẻ", callback_data=f"pbet2_xd_le_{amount}")]]
                await q.edit_message_text(f"Xóc Đĩa {amount:,}đ - Chọn:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
            elif game=="kbb":
                kb = [[InlineKeyboardButton(f, callback_data=f"pbet2_kbb_{f}_{amount}") for f in ['Kéo','Búa','Bao']]]
                await q.edit_message_text(f"KBB {amount:,}đ - Chọn:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
            elif game=="slot":
                await self.profile_slot(update, context, uid, amount)
        elif d.startswith("pbet2_"):
            parts = d.split('_'); game = parts[1]; choice = parts[2]; amount = int(parts[3])
            await self.profile_resolve(update, context, uid, game, choice, amount)
        elif d == "p_nap":
            tid = f"NAP{random.randint(100000,999999)}"
            db.pending[tid] = {"user_id":uid,"amount":100000,"time":datetime.now().isoformat()}
            db.save()
            await q.edit_message_text(f"📤 Yêu cầu nạp 100k, mã <code>{tid}</code>", parse_mode='HTML')

    async def profile_resolve(self, update, context, uid, game, choice, amount):
        p = get_player(uid)
        p['balance'] -= amount; p['daily_bet'] += amount
        if game=='taixiu':
            d, total, is_tai = Games.taixiu()
            dice_str = " ".join(emoji_dice(d))
            win = (choice=='T' and is_tai) or (choice=='X' and not is_tai)
            if win: p['balance'] += amount*2; txt=f"🎲 {dice_str} = {total} ({'TÀI' if is_tai else 'XỈU'})\n✅ +{amount*2:,}đ"
            else: txt=f"🎲 {dice_str} = {total} ({'TÀI' if is_tai else 'XỈU'})\n❌ -{amount:,}đ"
        elif game=='chanle':
            d, total, is_chan = Games.chanle()
            dice_str = " ".join(emoji_dice(d))
            win = (choice=='C' and is_chan) or (choice=='L' and not is_chan)
            if win: p['balance'] += amount*2; txt=f"🎯 {dice_str} = {total} ({'CHẴN' if is_chan else 'LẺ'})\n✅ +{amount*2:,}đ"
            else: txt=f"🎯 {dice_str} = {total} ({'CHẴN' if is_chan else 'LẺ'})\n❌ -{amount:,}đ"
        elif game=='baucua':
            result = Games.bau_cua()
            res_str = " ".join(emoji_bc(r) for r in result)
            win_count = result.count(int(choice))
            if win_count:
                win_amount = amount * (win_count+1)
                p['balance'] += win_amount
                txt=f"🦀 {res_str}\n✅ +{win_amount:,}đ ({win_count} mặt)"
            else: txt=f"🦀 {res_str}\n❌ -{amount:,}đ"
        elif game=='xocdia':
            coins = Games.xoc_dia()
            chan = coins.count('sấp')%2==0
            coin_str = " ".join(['🔵' if c=='sấp' else '🔴' for c in coins])
            win = (choice=='chan' and chan) or (choice=='le' and not chan)
            if win: p['balance'] += amount*2; txt=f"🥢 {coin_str} ({'CHẴN' if chan else 'LẺ'})\n✅ +{amount*2:,}đ"
            else: txt=f"🥢 {coin_str} ({'CHẴN' if chan else 'LẺ'})\n❌ -{amount:,}đ"
        elif game=='kbb':
            bot_choice, result = Games.kbb(choice.lower())
            if result=='win': p['balance'] += amount*2; txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Thắng +{amount*2:,}đ"
            elif result=='lose': txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Thua -{amount:,}đ"
            else: p['balance'] += amount; txt=f"✊ Bạn: {choice}, Bot: {bot_choice} → Hòa"
        db.save()
        await update.callback_query.edit_message_text(f"{txt}\n💰 <b>{p['balance']:,}đ</b>", parse_mode='HTML')

    async def profile_slot(self, update, context, uid, amount):
        p = get_player(uid)
        if p['balance'] < amount: await update.callback_query.answer("Không đủ tiền"); return
        p['balance'] -= amount
        result = Games.slot()
        if len(set(result))==1 and result[0]=='7️⃣': win_amount = amount*10
        elif len(set(result))==1: win_amount = amount*5
        elif result[0]==result[1] or result[1]==result[2]: win_amount = amount*2
        else: win_amount = 0
        p['balance'] += win_amount; db.save()
        txt = f"🎰 {' '.join(result)}\n"
        txt += f"✅ +{win_amount:,}đ" if win_amount else f"❌ -{amount:,}đ"
        txt += f"\n💰 {p['balance']:,}đ"
        await update.callback_query.edit_message_text(txt, parse_mode='HTML')

    def run(self):
        app = Application.builder().token(PROFILE_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.button))
        app.run_polling()

# ========== MAIN ==========
if __name__ == "__main__":
    print("🐊 CÁ XẤU ROOM v3 - KHỞI ĐỘNG 3 BOT")
    for bot in [AdminBot(), RoomBot(), ProfileBot()]:
        threading.Thread(target=bot.run, daemon=True).start()
    while True: time.sleep(1)
