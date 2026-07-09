import logging
import asyncio
import urllib.request
import xml.etree.ElementTree as ET
import json
import hashlib
import re
import os
import random
from datetime import datetime
from html import unescape

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== এনভায়রনমেন্ট ভেরিয়েবল ====================
from dotenv import load_dotenv
load_dotenv()

# ==================== Groq API ক্লায়েন্ট ====================
try:
    from groq import Groq
except ImportError:
    print("⚠️ Groq প্যাকেজ ইনস্টল করুন: pip install groq")
    Groq = None

# ==================== কনফিগারেশন ====================
TELEGRAM_TOKEN = os.environ.get("8891207870:AAENyw8YazdB3g9QEUhG0Ok_GPC6064KRRk")
CHAT_ID = os.environ.get("7602636366")
GROQ_API_KEY = os.environ.get("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")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN এবং CHAT_ID অবশ্যই সেট করুন!")

# লগিং সেটআপ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== RSS ফিড ====================
FEEDS = [
    ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ('The Verge - AI', 'https://www.theverge.com/rss/index.xml'),
    ('MIT Tech Review AI', 'https://www.technologyreview.com/feed/ai/'),
    ('Hacker News Top', 'https://hnrss.org/frontpage?points=100'),
]

# ==================== Groq AI কন্টেন্ট জেনারেটর ====================

class GroqAIContentGenerator:
    """Groq API ব্যবহার করে Agentic AI স্টাইলে কন্টেন্ট জেনারেট করে"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
        
        if Groq and api_key:
            try:
                self.client = Groq(api_key=api_key)
                logger.info("✅ Groq API কানেক্টেড!")
            except Exception as e:
                logger.error(f"❌ Groq API কানেক্ট করতে ব্যর্থ: {e}")
                self.client = None
        else:
            logger.warning("⚠️ Groq API Key সেট নেই। ফ্যালব্যাক মোড ব্যবহার হবে।")
            self.client = None
    
    def generate_post_with_groq(self, title, seo_story, source, is_old=False, desc="", story_url="#"):
        """Groq API ব্যবহার করে সম্পূর্ণ পোস্ট জেনারেট করে"""
        
        if not self.client:
            return self.generate_fallback_post(title, seo_story, source, is_old, story_url)
        
        try:
            prompt = self.create_prompt(title, seo_story, source, is_old, desc)
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """আপনি একজন অভিজ্ঞ কন্টেন্ট ক্রিয়েটর এবং ডিজিটাল মার্কেটার। 
                        আপনার কাজ হলো টেক নিউজকে আকর্ষণীয় ফেসবুক পোস্টে রূপান্তর করা।
                        
                        গুরুত্বপূর্ণ নিয়ম:
                        - সম্পূর্ণ বাংলায় লিখুন
                        - বন্ধুত্বপূর্ণ ও আকর্ষণীয় টোন
                        - রোবটিক বা অতিমাত্রায় ফরমাল হবেন না
                        - বড় প্যারাগ্রাফ এড়িয়ে চলুন
                        - ইমোজি ব্যবহার করুন (অতিরিক্ত না)
                        - মিথ্যা বা অবাস্তব দাবি করবেন না
                        - নিচের ফরম্যাটে উত্তর দিন"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-70b-8192",
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                stream=False
            )
            
            generated_content = chat_completion.choices[0].message.content
            img_prompt = generate_image_prompt(title, source)
            
            formatted_post = f"""{generated_content}

📌 সোর্স: {source}
🔗 {story_url}

---
🖼️ ইমেজ প্রম্পট: "{img_prompt}"
"""
            
            return formatted_post
            
        except Exception as e:
            logger.error(f"❌ Groq API ত্রুটি: {e}")
            return self.generate_fallback_post(title, seo_story, source, is_old, story_url)
    
    def create_prompt(self, title, seo_story, source, is_old, desc):
        """Groq-এর জন্য প্রম্পট তৈরি করে"""
        old_status = "পুরাতন" if is_old else "নতুন"
        
        prompt = f"""
খবরের শিরোনাম: {title}
খবরের বিবরণ: {seo_story}
খবরের সোর্স: {source}
খবরের স্ট্যাটাস: {old_status} খবর

এখন এই খবরটি নিচের ফরম্যাটে একটি ফেসবুক পোস্টে রূপান্তর করুন:

ফরম্যাট:
🔥 [একটি স্ক্রল-স্টপিং হুক - প্রথম লাইনেই মনোযোগ কাড়বে]

[একটি ন্যাচারাল ও এনগেজিং বডি - সরাসরি দর্শকের সাথে কথা বলবে]
[বেনিফিট হাইলাইট করুন - ফিচার না বলে সুবিধাগুলো বলুন]

💭 [একটি প্রশ্ন যা কমেন্ট উৎসাহিত করবে]

👉 [একটি স্ট্রং Call-to-Action]

হ্যাশট্যাগ: [৫-৮টি রিলেভেন্ট হ্যাশট্যাগ]

নিয়মাবলী:
১. সম্পূর্ণ বাংলায় লিখুন
২. বন্ধুত্বপূর্ণ ও আকর্ষণীয় টোন রাখুন
৩. রোবটিক বা ফরমাল হবেন না
৪. বড় প্যারাগ্রাফ এড়িয়ে চলুন
৫. স্বাভাবিকভাবে ইমোজি ব্যবহার করুন
৬. মিথ্যা দাবি করবেন না
৭. পোস্টটি ফেসবুকের জন্য উপযোগী করুন
"""
        return prompt
    
    def generate_fallback_post(self, title, seo_story, source, is_old=False, story_url="#"):
        """Groq না থাকলে ফ্যালব্যাক জেনারেটর"""
        
        hooks = [
            f"🚨 ব্রেকিং: {title[:30]}",
            f"⚡ শুনেছেন? {title[:30]}",
            f"🔥 গরম খবর: {title[:30]}",
            f"💥 চমক! {title[:30]}"
        ]
        hook = random.choice(hooks) + "!" if is_old else random.choice(hooks) + "!"
        
        source_names = {
            'TechCrunch AI': 'টেকক্রাঞ্চের', 
            'The Verge - AI': 'দ্য ভার্জের', 
            'MIT Tech Review AI': 'এমআইটি টেক রিভিউয়ের', 
            'Hacker News Top': 'হ্যাকার নিউজের'
        }
        src = source_names.get(source, source)
        
        body = f"{src} রিপোর্ট বলছে, {seo_story[:200]}। এই খবরটি সত্যিই গুরুত্বপূর্ণ!"
        
        benefits = [
            "🎁 **কী কী পাবেন?**",
            "  • 🤖 এআই আপনার কাজকে সহজ করবে",
            "  • ⏳ সময় বাঁচাবে অনেক",
            "  • 🎯 সঠিক সিদ্ধান্ত নিতে সাহায্য করবে"
        ]
        benefits_text = "\n".join(benefits)
        
        questions = [
            "💭 আপনি কি মনে করেন এই টেকনোলজি আমাদের জীবন পরিবর্তন করবে? 🤔",
            "💭 এই খবরটি আপনার জন্য কতটুকু প্রাসঙ্গিক? ⭐"
        ]
        question = random.choice(questions)
        
        ctas = [
            "👉 আপনার মতামত কমেন্টে জানান! 💬",
            "👉 বন্ধুদের সাথে শেয়ার করুন! 📤"
        ]
        cta = random.choice(ctas)
        
        hashtags = "#TechNews #AI #BanglaTech #Innovation #TechUpdate"
        
        old_header = "🔄 **পুনরায় শেয়ার করা হচ্ছে**\n\n" if is_old else ""
        img_prompt = generate_image_prompt(title, source)
        
        formatted_post = f"""{old_header}🔥 {hook}

{body}

{benefits_text}

{question}

{cta}

📌 সোর্স: {source}
🔗 {story_url}

{hashtags}

---
🖼️ ইমেজ প্রম্পট: "{img_prompt}"
"""
        return formatted_post

# ==================== ইমেজ প্রম্পট জেনারেটর ====================
def generate_image_prompt(title, source):
    """খবরের ভিত্তিতে বাস্তবসম্মত ইমেজ প্রম্পট তৈরি করে"""
    
    tech_keywords = []
    if 'AI' in title or 'artificial intelligence' in title.lower():
        tech_keywords.append('artificial intelligence')
    if 'chatgpt' in title.lower() or 'gpt' in title.lower():
        tech_keywords.append('ChatGPT')
    if 'google' in title.lower():
        tech_keywords.append('Google')
    if 'microsoft' in title.lower():
        tech_keywords.append('Microsoft')
    if 'apple' in title.lower():
        tech_keywords.append('Apple')
    if 'tesla' in title.lower() or 'elon' in title.lower():
        tech_keywords.append('Tesla')
    if 'robot' in title.lower():
        tech_keywords.append('robot')
    
    keywords_str = ' '.join(tech_keywords) if tech_keywords else 'technology news'
    
    prompts = [
        f"Professional news studio with {keywords_str} headline on digital screens, journalists working, modern broadcast setting, realistic documentary photography",
        f"Tech conference presentation about {keywords_str}, professional speakers, engaged audience, documentary style photography",
        f"Modern research lab with scientists discussing {keywords_str}, professional environment, realistic lighting",
        f"Digital innovation hub featuring {keywords_str}, creative professionals working, modern office, realistic photography"
    ]
    
    if 'TechCrunch' in source:
        prompts = [p + ", TechCrunch style" for p in prompts]
    elif 'The Verge' in source:
        prompts = [p + ", The Verge editorial style" for p in prompts]
    elif 'MIT' in source:
        prompts = [p + ", MIT research facility style" for p in prompts]
    elif 'Hacker' in source:
        prompts = [p + ", Silicon Valley startup style" for p in prompts]
    
    return random.choice(prompts)

# ==================== কোর ফাংশন ====================

def fetch_rss(url, max_items=5):
    """RSS ফিড থেকে খবর আনে"""
    stories = []
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw_data = response.read()
            try:
                xml_data = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                xml_data = raw_data.decode('latin-1', errors='ignore')
            
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item')[:max_items]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                desc = item.findtext('description', '').strip()
                
                if desc:
                    desc = re.sub(r'<[^>]+>', '', desc)
                    desc = desc.replace('<![[CDATA', '').replace(']]>', '').strip()
                
                if title and link:
                    stories.append({
                        'title': title.replace('<![[CDATA', '').replace(']]>', '').strip(),
                        'url': link,
                        'desc': desc if desc else ''
                    })
        return stories
    except Exception as e:
        logger.warning(f"⚠️ ফিড লোড ব্যর্থ: {url} - {e}")
        return []

def get_story_hash(title, url):
    """খবরের অনন্য আইডি তৈরি করে"""
    return hashlib.md5((title + url).lower().strip().encode()).hexdigest()[:16]

def load_state():
    """আগে পোস্ট করা খবরের তালিকা লোড করে"""
    state_file = 'state.json'
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'posted': {}}
    return {'posted': {}}

def save_state(state):
    """পোস্ট করা খবর সেভ করে"""
    with open('state.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def generate_seo_story(title, source, desc=""):
    """SEO ফ্রেন্ডলি স্টোরি তৈরি করে"""
    
    templates = [
        f"In a groundbreaking development, {title.lower()} has emerged as a game-changer in the tech world.",
        f"The tech industry is buzzing with excitement as {title.lower()} takes center stage.",
        f"Revolutionizing the tech landscape, {title.lower()} represents a significant leap forward."
    ]
    
    if desc and len(desc) > 10:
        sentences = desc.split('.')
        main_content = sentences[0] if sentences else ""
        if len(main_content) > 70:
            main_content = main_content[:70] + "..."
    else:
        main_content = f"This breakthrough in {title[:20].lower()} technology represents the next frontier."
    
    story_template = random.choice(templates)
    full_story = f"{story_template} {main_content}"
    
    if len(full_story.split()) > 100:
        full_story = ' '.join(full_story.split()[:100])
    
    final_story = full_story.strip()
    if not final_story.endswith(('.', '!', '?')):
        final_story += "."
    
    return final_story

def get_all_stories():
    """সব খবর আনে"""
    all_stories = []
    for name, feed_url in FEEDS:
        stories = fetch_rss(feed_url, max_items=5)
        for s in stories:
            s['source'] = name
        all_stories.extend(stories)

    state = load_state()
    posted = state.get('posted', {})
    
    now_ts = datetime.now().timestamp()
    cutoff_ts = now_ts - (30 * 24 * 60 * 60)
    for key in list(posted.keys()):
        if posted[key].get('ts', 0) < cutoff_ts:
            del posted[key]

    processed_stories = []
    for story in all_stories:
        h = get_story_hash(story['title'], story['url'])
        
        if h in posted:
            story['seo_story'] = posted[h].get('seo_story', generate_seo_story(story['title'], story['source'], story.get('desc', '')))
            story['img_prompt'] = posted[h].get('img_prompt', generate_image_prompt(story['title'], story['source']))
            story['is_old'] = True
        else:
            seo_story = generate_seo_story(story['title'], story['source'], story.get('desc', ''))
            img_prompt = generate_image_prompt(story['title'], story['source'])
            
            story['seo_story'] = seo_story
            story['img_prompt'] = img_prompt
            story['is_old'] = False
            
            posted[h] = {
                'title': story['title'], 
                'ts': now_ts,
                'seo_story': seo_story,
                'img_prompt': img_prompt
            }

    state['posted'] = posted
    save_state(state)
    
    return all_stories[:10]

# ==================== টেলিগ্রাম হ্যান্ডলার ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start কমান্ড"""
    if str(update.effective_chat.id) != CHAT_ID:
        await update.message.reply_text("⛔ এই বটটি শুধুমাত্র মালিকের জন্য।")
        return
    
    generator = GroqAIContentGenerator(GROQ_API_KEY)
    
    await update.message.reply_text(
        "🤖 **Groq AI নিউজ বট**\n\n"
        "আমি বিশ্বের সেরা টেক মিডিয়া থেকে খবর সংগ্রহ করি এবং সেগুলোকে আকর্ষণীয় ফেসবুক পোস্টে রূপান্তর করি।\n\n"
        "📌 **প্রতিটি পোস্টে থাকছে:**"
        "\n✅ স্ক্রল-স্টপিং হুক"
        "\n✅ ন্যাচারাল ও এনগেজিং বডি"
        "\n✅ বেনিফিট হাইলাইট"
        "\n✅ স্ট্রং CTA"
        "\n✅ ৫-৮টি হ্যাশট্যাগ"
        "\n\n⏳ খবর আনা হচ্ছে..."
    )
    
    all_stories = get_all_stories()
    
    if not all_stories:
        await update.message.reply_text("📭 কোনো খবর পাওয়া যায়নি।")
        return
    
    new_stories = [s for s in all_stories if not s.get('is_old', False)]
    old_stories = [s for s in all_stories if s.get('is_old', False)]
    
    if new_stories:
        await update.message.reply_text("🆕 **নতুন খবর:**", parse_mode='Markdown')
        for story in new_stories:
            post = generator.generate_post_with_groq(
                story['title'], 
                story['seo_story'], 
                story['source'], 
                False,
                story.get('desc', ''),
                story['url']
            )
            await update.message.reply_text(post, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    if old_stories:
        await update.message.reply_text("🔄 **পুরাতন খবর:**", parse_mode='Markdown')
        for story in old_stories:
            post = generator.generate_post_with_groq(
                story['title'], 
                story['seo_story'], 
                story['source'], 
                True,
                story.get('desc', ''),
                story['url']
            )
            await update.message.reply_text(post, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    total = len(all_stories)
    new_count = len(new_stories)
    old_count = len(old_stories)
    
    await update.message.reply_text(
        f"✅ **সফল!** {total}টি খবর পাঠানো হলো!\n"
        f"🆕 নতুন: {new_count}টি\n"
        f"🔄 পুরাতন: {old_count}টি\n\n"
        f"📊 প্রতিটি পোস্ট Groq AI দ্বারা জেনারেটেড।",
        parse_mode='Markdown'
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/news কমান্ড"""
    await start(update, context)

# ==================== মেইন ফাংশন ====================

def main():
    """বট চালু করুন"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news))
    
    logger.info("🤖 Groq AI News Bot চালু হচ্ছে...")
    logger.info(f"📱 চ্যাট আইডি: {CHAT_ID}")
    logger.info("💡 /start বা /news কমান্ড দিন")
    
    if GROQ_API_KEY:
        logger.info("✅ Groq API কনফিগার করা হয়েছে")
    else:
        logger.warning("⚠️ Groq API Key সেট নেই - ফ্যালব্যাক মোড চলবে")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()