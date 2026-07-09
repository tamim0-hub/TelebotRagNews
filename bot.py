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

# ==================== কনফিগারেশন ====================
TELEGRAM_TOKEN = "8891207870:AAENyw8YazdB3g9QEUhG0Ok_GPC6064KRRk"
CHAT_ID = "7602636366"

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

# ==================== AI হুক জেনারেটর ====================
def generate_ai_hook(title, source, seo_story):
    """কন্টেন্ট অনুযায়ী AI-জেনারেটেড হুক (হেডলাইন) তৈরি করে"""
    
    hook_templates = [
        lambda t, s: f"🚨 BREAKING: {t[:40]}...",
        lambda t, s: f"⚡ JUST IN: {t[:35]}...",
        lambda t, s: f"🔥 HOT NEWS: {t[:30]}...",
        lambda t, s: f"🤯 {t[:25]} - You Won't Believe This!",
        lambda t, s: f"😱 SHOCKING: {t[:30]}...",
        lambda t, s: f"💥 MIND-BLOWING: {t[:28]}...",
        lambda t, s: f"💡 {t[:35]} - Here's What You Need to Know",
        lambda t, s: f"📊 {t[:30]} - The Future is Here",
        lambda t, s: f"🎯 {t[:25]} - Game Changer Alert!",
        lambda t, s: f"🚀 {t[:30]} - Next Level Innovation",
        lambda t, s: f"💻 {t[:28]} - Tech Revolution Begins",
        lambda t, s: f"📱 {t[:25]} - The Future of Technology",
        lambda t, s: f"🎯 {t[:30]} - This Changes Everything",
        lambda t, s: f"🌟 {t[:25]} - A New Era Begins",
        lambda t, s: f"⚡ {t[:28]} - Game-Changing Development",
        lambda t, s: f"📢 ANNOUNCEMENT: {t[:35]}...",
        lambda t, s: f"📣 {t[:30]} - Major Update!",
        lambda t, s: f"🔔 {t[:25]} - Important News!",
        lambda t, s: f"🧠 {t[:30]} - The Smart Choice",
        lambda t, s: f"💡 {t[:25]} - Innovation Unleashed",
        lambda t, s: f"🌟 {t[:28]} - The Future is Now",
    ]
    
    keywords = []
    important_words = ['AI', 'artificial intelligence', 'machine learning', 'tech', 'innovation', 
                       'breakthrough', 'revolution', 'future', 'Google', 'Microsoft', 'Apple',
                       'Amazon', 'Facebook', 'Meta', 'Tesla', 'OpenAI', 'ChatGPT', 'GPT']
    
    for word in important_words:
        if word.lower() in title.lower() or word.lower() in seo_story.lower():
            keywords.append(word)
    
    if not keywords:
        hook_func = random.choice(hook_templates)
        return hook_func(title, source)
    
    main_keyword = keywords[0]
    if main_keyword in ['AI', 'artificial intelligence']:
        templates = [
            f"🤖 AI BREAKTHROUGH: {title[:35]} - The Future is Here!",
            f"🧠 AI Revolution: {title[:30]} - Game Changer!",
            f"⚡ AI Innovation: {title[:35]} - Next Level Technology",
        ]
    elif main_keyword in ['Google', 'Microsoft', 'Apple']:
        templates = [
            f"🚀 {main_keyword} Just Changed Everything: {title[:35]}",
            f"💥 {main_keyword} News: {title[:30]} - Big Update!",
            f"🎯 {main_keyword} Innovation: {title[:35]} - You Need to Know",
        ]
    elif main_keyword in ['ChatGPT', 'OpenAI', 'GPT']:
        templates = [
            f"🤯 ChatGPT Just Got Smarter: {title[:35]}",
            f"⚡ OpenAI News: {title[:30]} - Revolutionary Update!",
            f"💡 ChatGPT Evolution: {title[:35]} - Game Changer",
        ]
    elif main_keyword in ['Tesla', 'Elon Musk']:
        templates = [
            f"🚗 Tesla News: {title[:35]} - The Future of Driving",
            f"⚡ Elon Musk Just Announced: {title[:30]}",
            f"🔥 Tesla Innovation: {title[:35]} - Revolutionary!",
        ]
    else:
        templates = [
            f"🔥 {main_keyword} News: {title[:40]}...",
            f"⚡ {main_keyword} Update: {title[:35]}...",
            f"📢 {main_keyword} Breakthrough: {title[:30]}...",
        ]
    
    custom_hook = random.choice(templates)
    
    if len(custom_hook) > 60:
        custom_hook = custom_hook[:57] + "..."
    
    return custom_hook

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
    if 'innovation' in title.lower() or 'breakthrough' in title.lower():
        tech_keywords.append('innovation')
    
    keywords_str = ' '.join(tech_keywords) if tech_keywords else 'technology news'
    
    prompts = [
        f"Professional news studio with {keywords_str} headline on digital screens, journalists working, modern broadcast setting, realistic documentary photography",
        f"Tech conference presentation about {keywords_str}, professional speakers, engaged audience, documentary style photography",
        f"Modern research lab with scientists discussing {keywords_str}, professional environment, realistic lighting, National Geographic style",
        f"Digital innovation hub featuring {keywords_str}, creative professionals working, modern office, realistic photography",
        f"Technology breakthrough moment with {keywords_str}, scientists celebrating, professional news photography style",
        f"High-tech workspace with {keywords_str} development, professional team collaborating, realistic documentary style",
        f"Futuristic technology center showcasing {keywords_str}, professional setting, realistic architectural photography",
        f"Professional tech journalists reporting on {keywords_str}, modern newsroom, realistic broadcast photography"
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

# ==================== ফেসবুক ক্যাপশন জেনারেটর ====================
def generate_facebook_caption(story):
    """
    ফেসবুকের জন্য আকর্ষণীয় ক্যাপশন তৈরি করে
    Format: হুক → বডি → সুবিধা → CTA → হ্যাশট্যাগ
    """
    title = story['title']
    source = story['source']
    seo_story = story.get('seo_story', title)
    
    # ----- ১. স্ক্রল-স্টপিং হুক (প্রথম লাইন) -----
    hooks = [
        f"🚨 {title[:50]}… এটা কিন্তু আপনি মিস করবেন না!",
        f"😱 চমকে যাওয়ার মতো খবর! {title[:45]}…",
        f"💥 শুধু এই একটা খবর পড়লেই আজকের আপডেট শেষ! {title[:40]}…",
        f"🤯 কী বলা যায়! {title[:50]}…",
        f"🔥 ব্রেকিং: {title[:45]}… বিস্তারিত দেখুন!",
        f"⚡ এখনই পড়ুন: {title[:50]}…",
        f"📢 {title[:50]} – পুরো স্টোরি দিচ্ছি!",
        f"🎯 আপনার জন্য বড় খবর! {title[:45]}…",
    ]
    
    # গুরুত্বপূর্ণ কীওয়ার্ড অনুযায়ী কাস্টম হুক
    important_words = ['AI', 'ChatGPT', 'OpenAI', 'Google', 'Microsoft', 'Apple', 'Tesla']
    main_keyword = None
    for word in important_words:
        if word.lower() in title.lower():
            main_keyword = word
            break
    
    if main_keyword == 'AI':
        hooks.insert(0, f"🤖 এই AI খবরটা পড়ে নিন! {title[:45]}…")
    elif main_keyword == 'ChatGPT':
        hooks.insert(0, f"💬 ChatGPT নিয়ে বড় আপডেট! {title[:45]}…")
    elif main_keyword == 'Google':
        hooks.insert(0, f"🔍 গুগল আবার কী করলো! {title[:45]}…")
    elif main_keyword == 'Tesla':
        hooks.insert(0, f"🚗 টেসলা ফ্যান? আপনার জন্য খবর! {title[:45]}…")
    
    hook = random.choice(hooks)
    
    # ----- ২. প্রাকৃতিক ও আকর্ষণীয় বডি -----
    # SEO স্টোরি থেকে প্রথম ১-২ বাক্য নিন
    sentences = seo_story.split('.')
    body_parts = []
    
    for sent in sentences[:3]:
        clean = sent.strip()
        if len(clean) > 10:
            body_parts.append(clean)
    
    body_text = '. '.join(body_parts[:2])
    if not body_text.endswith('.'):
        body_text += '.'
    
    # যদি বডি খুব ছোট হয়, তাহলে এক্সট্রা লাইন যোগ করুন
    if len(body_text.split()) < 15:
        extra = random.choice([
            f"এটি কিন্তু শুধু খবর নয়, এটি আপনার জন্য গুরুত্বপূর্ণ আপডেট।",
            f"বিশ্বের বড় মিডিয়া এখন এই নিয়ে আলোচনা করছে।",
            f"আপনি যদি টেকপ্রেমী হন, তাহলে এই খবর আপনার জানা উচিত।",
        ])
        body_text = f"{body_text} {extra}"
    
    # ----- ৩. প্রধান সুবিধা হাইলাইট (পণ্য/খবর থেকে লাভ) -----
    benefits = [
        f"💡 এই খবর থেকে আপনি জানতে পারবেন – কীভাবে এই উন্নয়ন আপনার জীবনকে সহজ করবে।",
        f"✅ এই আপডেট আপনার কাজের গতি বাড়াতে পারে, সময় বাঁচাতে পারে।",
        f"🎯 জানা থাকলে আপনি সবাই থেকে এক ধাপ এগিয়ে থাকবেন।",
        f"🔥 এই ট্রেন্ড ধরতে পারলে আপনি অনেক কিছু মিস করবেন না।",
        f"💪 এই খবর শুধু খবর নয়, এটি আপনার ভবিষ্যতের জন্য গুরুত্বপূর্ণ।",
    ]
    benefit = random.choice(benefits)
    
    # ----- ৪. শক্তিশালী CTA -----
    cta_options = [
        f"\n👉 আপনার কী মনে হচ্ছে? কমেন্টে জানান! আর হ্যাঁ, ফ্রেন্ডদেরও শেয়ার করে দিন যারা টেক নিয়ে আগ্রহী।",
        f"\n📢 আপনার বন্ধুকে জানান! আর আপনার মতামত দিন – এই খবরে আপনি কী দেখলেন?",
        f"\n💬 নিচে কমেন্টে বলুন – এই খবরটা আপনার কাজে লাগবে? আর হ্যাঁ, শেয়ার করতে ভুলবেন না!",
        f"\n🚀 আপনার কি জানা ছিল? কমেন্টে জানান! আর যাদের জানা দরকার তাদের শেয়ার করুন।",
        f"\n🔥 আপনার ফ্রেন্ডদেরও জানান! আর বলুন – এই খবরটা কেমন লাগলো আপনার?",
    ]
    cta = random.choice(cta_options)
    
    # ----- ৫. হ্যাশট্যাগ (৫-৮টি) -----
    source_tag = source.replace(' ', '').replace('-', '')
    hashtags = [
        f"#{source_tag}",
        "#TechNews",
        "#AI",
        "#BanglaTech",
        "#Innovation",
        "#FutureTech",
        "#Trending",
        "#BreakingNews"
    ]
    
    # খবরের বিষয় অনুযায়ী কাস্টম হ্যাশট্যাগ
    if 'AI' in title or 'artificial intelligence' in title.lower():
        hashtags.append("#ArtificialIntelligence")
    if 'ChatGPT' in title or 'GPT' in title:
        hashtags.append("#ChatGPT")
    if 'Google' in title:
        hashtags.append("#Google")
    if 'Microsoft' in title:
        hashtags.append("#Microsoft")
    if 'Apple' in title:
        hashtags.append("#Apple")
    if 'Tesla' in title or 'Elon' in title:
        hashtags.append("#Tesla")
    
    # ডুপ্লিকেট রিমুভ করে ৮টার বেশি না রাখি
    hashtags = list(dict.fromkeys(hashtags))[:8]
    hashtag_text = ' '.join(hashtags)
    
    # ----- ফাইনাল ক্যাপশন তৈরি (২৫০ শব্দের মধ্যে) -----
    caption_parts = [
        hook,
        "",
        body_text,
        "",
        benefit,
        "",
        cta,
        "",
        hashtag_text
    ]
    
    caption = '\n'.join(caption_parts)
    
    # শব্দ গণনা (২৫০-এর মধ্যে রাখতে)
    word_count = len(caption.split())
    if word_count > 250:
        # বডি ছোট করুন
        short_body = '. '.join(body_parts[:1])
        if not short_body.endswith('.'):
            short_body += '.'
        caption_parts[2] = short_body
        caption = '\n'.join(caption_parts)
    
    return caption

# ==================== কোর ফাংশন ====================

def fetch_rss(url, max_items=5):
    """RSS ফিড থেকে খবর আনে - এখন বেশি খবর আনে"""
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
    """SEO ফ্রেন্ডলি স্টোরি টেলিং মোডে কন্টেন্ট তৈরি করে"""
    
    templates = [
        f"In a groundbreaking development, {title.lower()} has emerged as a game-changer in the tech world. This innovation promises to reshape how we interact with technology daily.",
        f"The tech industry is buzzing with excitement as {title.lower()} takes center stage. This latest advancement demonstrates the incredible pace of innovation in the digital age.",
        f"Revolutionizing the tech landscape, {title.lower()} represents a significant leap forward. Experts are calling this a defining moment in technological evolution.",
        f"Breaking new ground in the world of technology, {title.lower()} has captured the attention of industry leaders worldwide. This development could transform the future of digital innovation.",
        f"In a remarkable display of technological progress, {title.lower()} showcases the brilliant minds behind modern innovation. This advancement could change the way we live and work."
    ]
    
    if desc and len(desc) > 10:
        sentences = desc.split('.')
        main_content = sentences[0] if sentences else ""
        if len(main_content) > 70:
            main_content = main_content[:70] + "..."
    else:
        main_content = f"This breakthrough in {title[:20].lower()} technology represents the next frontier in digital innovation and artificial intelligence."
    
    story_template = random.choice(templates)
    full_story = f"{story_template} {main_content}"
    
    words = len(full_story.split())
    if words > 100:
        full_story = ' '.join(full_story.split()[:100])
    elif words < 90:
        extra = random.choice([
            f"This development in {title.split()[0] if title.split() else 'technology'} could have far-reaching implications for the future.",
            f"As the tech community continues to explore these possibilities, the potential applications seem limitless.",
            f"This achievement marks another milestone in the rapid evolution of technology."
        ])
        full_story = f"{full_story} {extra}"
    
    final_story = full_story.strip()
    if not final_story.endswith(('.', '!', '?')):
        final_story += "."
    
    return final_story

def get_all_stories():
    """সব খবর আনে - নতুন এবং পুরাতন সব"""
    all_stories = []
    for name, feed_url in FEEDS:
        # এখন প্রতিটি ফিড থেকে ৫টি করে খবর আনে (আগে ছিল ৩টি)
        stories = fetch_rss(feed_url, max_items=5)
        for s in stories:
            s['source'] = name
        all_stories.extend(stories)

    state = load_state()
    posted = state.get('posted', {})
    
    # ৩০ দিনের বেশি পুরোনো খবর ডিলিট করে দিন (আগে ছিল ৭ দিন)
    now_ts = datetime.now().timestamp()
    cutoff_ts = now_ts - (30 * 24 * 60 * 60)
    for key in list(posted.keys()):
        if posted[key].get('ts', 0) < cutoff_ts:
            del posted[key]

    # সব খবর প্রসেস করুন (নতুন + পুরাতন)
    processed_stories = []
    for story in all_stories:
        h = get_story_hash(story['title'], story['url'])
        
        # চেক করুন খবরটি আগে পোস্ট হয়েছে কিনা
        if h in posted:
            # পুরাতন খবর - state থেকে ডাটা নিন
            story['seo_story'] = posted[h].get('seo_story', generate_seo_story(story['title'], story['source'], story.get('desc', '')))
            story['ai_hook'] = posted[h].get('ai_hook', generate_ai_hook(story['title'], story['source'], story['seo_story']))
            story['img_prompt'] = posted[h].get('img_prompt', generate_image_prompt(story['title'], story['source']))
            story['is_old'] = True  # পুরাতন খবর চিহ্নিত
        else:
            # নতুন খবর - নতুন করে সব তৈরি করুন
            seo_story = generate_seo_story(story['title'], story['source'], story.get('desc', ''))
            ai_hook = generate_ai_hook(story['title'], story['source'], seo_story)
            img_prompt = generate_image_prompt(story['title'], story['source'])
            
            story['seo_story'] = seo_story
            story['ai_hook'] = ai_hook
            story['img_prompt'] = img_prompt
            story['is_old'] = False  # নতুন খবর চিহ্নিত
            
            # স্টেটে সেভ করুন
            posted[h] = {
                'title': story['title'], 
                'ts': now_ts,
                'seo_story': seo_story,
                'ai_hook': ai_hook,
                'img_prompt': img_prompt
            }

    state['posted'] = posted
    save_state(state)
    
    # সব খবর রিটার্ন করুন (সর্বোচ্চ ১০টি)
    return all_stories[:10]

def format_telegram_message(story):
    """টেলিগ্রামের জন্য মেসেজ ফরম্যাট করে - এখন ফেসবুক ক্যাপশন যোগ করা হয়েছে"""
    
    hook = story.get('ai_hook', f"🔥 {story['title'][:40]}")
    seo_content = story.get('seo_story', story['title'])
    img_prompt = story.get('img_prompt', f"Technology news story about {story['title'][:30]}")
    fb_caption = generate_facebook_caption(story)  # নতুন ফেসবুক ক্যাপশন
    
    # পুরাতন/নতুন চিহ্নিত করুন
    status_emoji = "🔄" if story.get('is_old', False) else "🆕"
    status_text = "পুনরায়" if story.get('is_old', False) else "নতুন"
    
    message = f"""{hook}

📝 {seo_content}

🖼️ ইমেজ প্রম্পট: 
"{img_prompt}"

📌 সোর্স: {story['source']}
🔗 {story['url']}
{status_emoji} স্ট্যাটাস: {status_text} খবর

━━━━━━━━━━━━━━━━━━━━
📱 **ফেসবুকের জন্য ক্যাপশন:**
━━━━━━━━━━━━━━━━━━━━
{fb_caption}

#TechNews #AI #{story['source'].replace(' ', '')} #Innovation #BreakingNews
"""
    
    return message

# ==================== টেলিগ্রাম হ্যান্ডলার ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start কমান্ড হ্যান্ডলার - এখন সব খবর দেখায়"""
    if str(update.effective_chat.id) != CHAT_ID:
        await update.message.reply_text("⛔ এই বটটি শুধুমাত্র মালিকের জন্য।")
        return
    
    await update.message.reply_text(
        "🚀 **AI News Bot**\n\n"
        "আমি বিশ্বের শীর্ষস্থানীয় টেক মিডিয়া থেকে AI সম্পর্কিত খবর সংগ্রহ করি।\n\n"
        "📌 বিশেষত্ব:"
        "\n✅ নতুন + পুরাতন সব খবর"
        "\n✅ AI-জেনারেটেড হুক"
        "\n✅ SEO ফ্রেন্ডলি কন্টেন্ট"
        "\n✅ স্টোরি টেলিং স্টাইলে"
        "\n✅ ৯০-১০০ শব্দের মধ্যে"
        "\n✅ বাস্তবসম্মত ইমেজ প্রম্পট"
        "\n✅ ফেসবুকের জন্য আকর্ষণীয় ক্যাপশন"
        "\n\n⏳ সব খবর আনা হচ্ছে, একটু অপেক্ষা করুন..."
    )
    
    # সব খবর আনুন (নতুন + পুরাতন)
    all_stories = get_all_stories()
    
    if not all_stories:
        await update.message.reply_text(
            "📭 কোনো খবর পাওয়া যায়নি।\n\n"
            "🔄 কিছুক্ষণ পরে আবার /start দিন অথবা /news কমান্ড ব্যবহার করুন।"
        )
        return
    
    # নতুন এবং পুরাতন খবর আলাদা করুন
    new_stories = [s for s in all_stories if not s.get('is_old', False)]
    old_stories = [s for s in all_stories if s.get('is_old', False)]
    
    # প্রথমে নতুন খবর পাঠান
    if new_stories:
        await update.message.reply_text("🆕 **নতুন খবর:**", parse_mode='Markdown')
        for story in new_stories:
            message = format_telegram_message(story)
            await update.message.reply_text(message, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    # তারপর পুরাতন খবর পাঠান
    if old_stories:
        await update.message.reply_text("🔄 **পুরাতন খবর (পুনরায়):**", parse_mode='Markdown')
        for story in old_stories:
            message = format_telegram_message(story)
            await update.message.reply_text(message, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    # সারাংশ
    total = len(all_stories)
    new_count = len(new_stories)
    old_count = len(old_stories)
    
    await update.message.reply_text(
        f"✅ **সফল!** মোট {total}টি খবর পাঠানো হলো!\n"
        f"🆕 নতুন: {new_count}টি\n"
        f"🔄 পুরাতন: {old_count}টি\n\n"
        f"📊 প্রতিটি খবর AI-জেনারেটেড হুক এবং SEO অপটিমাইজড।\n"
        f"🔄 নতুন খবর পেতে আবার /start দিন।",
        parse_mode='Markdown'
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/news কমান্ড - /start এর মতোই কাজ করে"""
    await start(update, context)

# ==================== মেইন ফাংশন ====================

def main():
    """বট চালু করুন"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news))
    
    logger.info("🤖 AI News Bot চালু হচ্ছে...")
    logger.info(f"📱 চ্যাট আইডি: {CHAT_ID}")
    logger.info("💡 /start বা /news কমান্ড দিয়ে নতুন + পুরাতন সব খবর পাবেন")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()