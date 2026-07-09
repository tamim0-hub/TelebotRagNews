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
TELEGRAM_TOKEN = "8891207870:AAHIkv2K5szrlk9uQQUduG755pG3ncy8iWc"
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

# ==================== Agentic AI কন্টেন্ট জেনারেটর ====================

class AgenticAIContentGenerator:
    """Agentic AI স্টাইলে কন্টেন্ট জেনারেট করে"""
    
    def __init__(self):
        self.hook_templates = [
            "🚨 ব্রেকিং: {title}",
            "⚡ শুনেছেন কি? {title}",
            "🔥 গরম খবর: {title}",
            "💥 চমক! {title}",
            "🤯 অবিশ্বাস্য! {title}",
            "🎯 লক্ষ্য করুন: {title}",
            "🌟 নতুন আপডেট: {title}",
            "📢 জেনে নিন: {title}",
            "💡 জানেন কি? {title}",
            "🚀 বড় খবর: {title}"
        ]
        
        self.cta_templates = [
            "আপনার কি মতামত? কমেন্টে জানান! 💬",
            "এই খবর সম্পর্কে আপনার কী ধারণা? নিচে লিখুন 👇",
            "আপনি কি এই টেকনোলজি ব্যবহার করবেন? জানাতে ভুলবেন না! 😊",
            "এই খবরটি আপনার বন্ধুদের সাথে শেয়ার করুন! 📤",
            "আরও এরকম আপডেট পেতে পেজটি ফলো করুন! 👍",
            "এই খবরটি কীভাবে কাজে লাগাতে পারেন? কমেন্টে বলুন! 💭",
            "আপনার কি মনে হয়? আমাদের জানান! ✍️"
        ]
        
        self.benefit_templates = [
            "এর মাধ্যমে আপনি সময় বাঁচাতে পারবেন 🕐",
            "এটি আপনার কাজের গতি বাড়াবে 🚀",
            "টেকনোলজিটি আপনার জীবনকে সহজ করবে 💡",
            "এটি নতুন দিগন্ত উন্মোচন করবে 🌅",
            "আপনি এর মাধ্যমে বেশি দক্ষ হতে পারবেন 🎯",
            "এটি আপনার সৃজনশীলতা বাড়াবে 🎨",
            "আপনি এর থেকে শিখতে পারবেন অনেক কিছু 📚"
        ]
        
        self.engagement_questions = [
            "আপনি কি মনে করেন এই টেকনোলজি আমাদের জীবন পরিবর্তন করবে? 🤔",
            "এই খবরটি আপনার জন্য কতটুকু প্রাসঙ্গিক? ⭐",
            "আপনি কি এই টেকনোলজি ব্যবহার করতে আগ্রহী? 💭",
            "আপনার কি এই বিষয়ে কোনো অভিজ্ঞতা আছে? শেয়ার করুন! 📖",
            "আপনি কি এই খবরটি আগে শুনেছেন? 🗣️"
        ]
    
    def generate_scroll_stopping_hook(self, title, is_old=False):
        """Scroll-stopping hook তৈরি করে - প্রথম লাইনেই মনোযোগ কাড়ে"""
        hook_prefix = random.choice(self.hook_templates)
        hook = hook_prefix.format(title=title[:35])
        
        # পুরাতন খবরের জন্য আলাদা হুক
        if is_old:
            old_hooks = [
                f"🔄 মনে পড়ে? {title[:30]}",
                f"📌 গুরুত্বপূর্ণ রিমাইন্ডার: {title[:30]}",
                f"🔙 ফিরে দেখা: {title[:30]}",
                f"⏳ সময়ের সেরা খবর: {title[:30]}"
            ]
            hook = random.choice(old_hooks)
        
        # হুককে আরও আকর্ষণীয় করা
        if not hook.endswith(('!', '?', '।')):
            hook += "!"
            
        return hook
    
    def generate_natural_body(self, title, seo_story, source, is_old=False):
        """Natural এবং engaging body তৈরি করে - সরাসরি দর্শকের সাথে কথা বলে"""
        
        # সোর্স অনুযায়ী পরিচয়
        source_intros = {
            'TechCrunch AI': 'টেকক্রাঞ্চের', 
            'The Verge - AI': 'দ্য ভার্জের', 
            'MIT Tech Review AI': 'এমআইটি টেক রিভিউয়ের', 
            'Hacker News Top': 'হ্যাকার নিউজের'
        }
        source_name = source_intros.get(source, source)
        
        bodies = []
        
        # বিভিন্ন স্টাইলের বডি
        body_templates = [
            f"আজকের টেক দুনিয়ায় {title[:20]} নিয়ে আলোচনা চলছে। {source_name} রিপোর্ট বলছে, {seo_story[:80]}। এই খবরটি সত্যিই চমকপ্রদ!",
            
            f"বন্ধুরা, {title[:20]} বিষয়টি আমার দৃষ্টি কেড়েছে। {source_name} মতে, {seo_story[:80]}। এটা নিয়ে আমাদের ভাবনা উচিত।",
            
            f"আমি যখন {title[:20]} খবরটা দেখলাম, মনে হলো এইটা শেয়ার না করে পারছি না! {source_name} বলছে, {seo_story[:80]}। আপনার কী মতামত?",
            
            f"আপনি কি জানেন? {title[:20]} প্রযুক্তি দুনিয়ায় আলোড়ন ফেলেছে। {source_name} এর বিশ্লেষণ বলছে, {seo_story[:80]}। এটা আসলেই গুরুত্বপূর্ণ!",
            
            f"টেকনোলজি প্রেমীদের জন্য বড় খবর! {title[:20]} নিয়ে {source_name} প্রকাশ করেছে প্রতিবেদন। {seo_story[:80]}। এইটা মিস করবেন না!",
            
            f"আজকের আলোচনার বিষয় {title[:20]}। {source_name} এর মতে, {seo_story[:80]}। আপনার কী মনে হয়, এই টেকনোলজি কি কাজে আসবে?"
        ]
        
        # এলোমেলোভাবে বডি বাছাই
        body = random.choice(body_templates)
        
        # পুরাতন খবরের জন্য আলাদা বডি
        if is_old:
            old_bodies = [
                f"আপনি কি {title[:20]} খবরটি মনে আছে? {source_name} রিপোর্টটি আবার পড়ে দেখি, {seo_story[:80]}। এই খবরটি এখনো প্রাসঙ্গিক!",
                f"পুরনো হলেও গুরুত্বপূর্ণ! {title[:20]} নিয়ে {source_name} বলেছিল, {seo_story[:80]}। এটা ভুলে গেলে চলবে না!",
                f"আমার মনে পড়ে যখন {title[:20]} খবরটি প্রথম এলো। {source_name} এর সেই প্রতিবেদনে ছিল, {seo_story[:80]}। এখনো কাজে লাগবে!"
            ]
            body = random.choice(old_bodies)
        
        return body
    
    def highlight_benefits(self, title, seo_story):
        """Features না বলে Benefits হাইলাইট করে"""
        benefits = []
        
        # খবরের ধরণ অনুযায়ী বেনিফিট বাছাই
        if 'AI' in title or 'artificial' in title.lower():
            benefits = [
                "🤖 এআই আপনার কাজকে সহজ করবে",
                "⏳ সময় বাঁচাবে অনেক",
                "🎯 সঠিক সিদ্ধান্ত নিতে সাহায্য করবে",
                "💡 নতুন চিন্তার দিগন্ত খুলবে",
                "📈 দক্ষতা বাড়াবে বহুগুণ"
            ]
        elif 'ChatGPT' in title or 'GPT' in title:
            benefits = [
                "💬 কথোপকথনে নতুন মাত্রা",
                "📝 কন্টেন্ট তৈরি করবে দ্রুত",
                "🎨 ক্রিয়েটিভিটি বাড়াবে",
                "🧠 শেখার অভিজ্ঞতা উন্নত করবে",
                "🌍 ভাষার বাধা দূর করবে"
            ]
        elif 'Google' in title:
            benefits = [
                "🔍 তথ্য খোঁজা হবে সহজ",
                "⚡ দ্রুত কাজ করার সুযোগ",
                "📱 যেকোনো ডিভাইসে ব্যবহার",
                "🌐 বিশ্বের সাথে সংযুক্ত থাকা",
                "💡 নতুন আইডিয়া পেতে সাহায্য"
            ]
        else:
            # জেনেরিক বেনিফিট
            benefits = [
                "🚀 আপনার কাজের গতি বাড়াবে",
                "💡 নতুন কিছু শেখার সুযোগ",
                "🎯 লক্ষ্য পৌঁছাতে সহায়তা",
                "⭐ অভিজ্ঞতা উন্নত করবে",
                "🌟 জীবনে নতুন দিক দেখাবে"
            ]
        
        # এলোমেলোভাবে ২-৩টি বেনিফিট বাছাই
        selected_benefits = random.sample(benefits, min(3, len(benefits)))
        benefits_text = '\n'.join(f"  • {b}" for b in selected_benefits)
        
        return f"🎁 **কী কী পাবেন?**\n{benefits_text}"
    
    def generate_cta(self, is_old=False):
        """Strong Call-to-Action তৈরি করে"""
        cta = random.choice(self.cta_templates)
        
        # পুরাতন খবরের জন্য আলাদা CTA
        if is_old:
            old_cta = [
                "এই খবরটি আপনার বন্ধুদের সাথে শেয়ার করুন! 📤",
                "আপনার কী মনে আছে এই খবরটি সম্পর্কে? কমেন্টে বলুন! 💬",
                "এই খবরটি কি আপনার কাজে এসেছে? জানাতে ভুলবেন না! 😊",
                "আরও পুরাতন খবর পেতে ফলো করুন! 👍"
            ]
            cta = random.choice(old_cta)
            
        return cta
    
    def generate_hashtags(self, title, source, is_old=False):
        """৫-৮টি relevant হ্যাশট্যাগ তৈরি করে"""
        base_tags = ['#TechNews', '#AI', '#BanglaTech', '#Innovation']
        source_tags = {
            'TechCrunch AI': ['#TechCrunch'],
            'The Verge - AI': ['#TheVerge'],
            'MIT Tech Review AI': ['#MIT', '#TechReview'],
            'Hacker News Top': ['#HackerNews']
        }
        
        # টাইটেল থেকে কীওয়ার্ড এক্সট্রাক্ট
        keyword_tags = []
        if 'AI' in title or 'artificial' in title.lower():
            keyword_tags.append('#ArtificialIntelligence')
        if 'Google' in title:
            keyword_tags.append('#Google')
        if 'Microsoft' in title:
            keyword_tags.append('#Microsoft')
        if 'ChatGPT' in title or 'GPT' in title:
            keyword_tags.append('#ChatGPT')
        if 'Tesla' in title or 'Elon' in title:
            keyword_tags.append('#Tesla')
        if 'robot' in title.lower():
            keyword_tags.append('#Robotics')
        if 'data' in title.lower():
            keyword_tags.append('#DataScience')
        
        # সোর্স ট্যাগ
        source_tag = source_tags.get(source, ['#TechUpdate'])
        
        # সব ট্যাগ একত্রিত করা
        all_tags = base_tags + keyword_tags + source_tag
        
        # পুরাতন খবরের জন্য আলাদা ট্যাগ
        if is_old:
            old_tags = ['#Throwback', '#OldButGold', '#RememberThis']
            all_tags.extend(old_tags)
        
        # ডুপ্লিকেট রিমুভ এবং ৫-৮টি ট্যাগ বাছাই
        unique_tags = list(dict.fromkeys(all_tags))
        selected_tags = random.sample(unique_tags, min(random.randint(5, 8), len(unique_tags)))
        
        return ' '.join(selected_tags)
    
    def generate_engagement_question(self):
        """Comment উৎসাহিত করার প্রশ্ন তৈরি করে"""
        return random.choice(self.engagement_questions)
    
    def generate_full_post(self, story, is_old=False):
        """সম্পূর্ণ পোস্ট তৈরি করে - দেওয়া ফরম্যাট অনুযায়ী"""
        
        title = story['title']
        seo_story = story.get('seo_story', title)
        source = story['source']
        
        # ১. Scroll-stopping hook
        hook = self.generate_scroll_stopping_hook(title, is_old)
        
        # ২. Natural engaging body
        body = self.generate_natural_body(title, seo_story, source, is_old)
        
        # ৩. Benefits highlight
        benefits = self.highlight_benefits(title, seo_story)
        
        # ৪. Strong CTA
        cta = self.generate_cta(is_old)
        
        # ৫. Engagement question
        question = self.generate_engagement_question()
        
        # ৬. Hashtags
        hashtags = self.generate_hashtags(title, source, is_old)
        
        # ৭. ইমেজ প্রম্পট (আগের মতো)
        img_prompt = story.get('img_prompt', generate_image_prompt(title, source))
        
        # ফাইনাল ফরম্যাট
        formatted_post = f"""🔥 {hook}

{body}

{benefits}

💭 {question}

👉 {cta}

📌 সোর্স: {source}
🔗 {story['url']}

{hashtags}

---
🖼️ ইমেজ প্রম্পট: "{img_prompt}"
"""
        
        # পুরাতন খবরের জন্য আলাদা হেডার
        if is_old:
            formatted_post = f"🔄 **পুনরায় শেয়ার করা হচ্ছে**\n\n" + formatted_post
        
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
    if 'innovation' in title.lower() or 'breakthrough' in title.lower():
        tech_keywords.append('innovation')
    
    keywords_str = ' '.join(tech_keywords) if tech_keywords else 'technology news'
    
    prompts = [
        f"Professional news studio with {keywords_str} headline on digital screens, journalists working, modern broadcast setting, realistic documentary photography",
        f"Tech conference presentation about {keywords_str}, professional speakers, engaged audience, documentary style photography",
        f"Modern research lab with scientists discussing {keywords_str}, professional environment, realistic lighting",
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
        stories = fetch_rss(feed_url, max_items=5)
        for s in stories:
            s['source'] = name
        all_stories.extend(stories)

    state = load_state()
    posted = state.get('posted', {})
    
    # ৩০ দিনের বেশি পুরোনো খবর ডিলিট করে দিন
    now_ts = datetime.now().timestamp()
    cutoff_ts = now_ts - (30 * 24 * 60 * 60)
    for key in list(posted.keys()):
        if posted[key].get('ts', 0) < cutoff_ts:
            del posted[key]

    # সব খবর প্রসেস করুন
    processed_stories = []
    for story in all_stories:
        h = get_story_hash(story['title'], story['url'])
        
        if h in posted:
            # পুরাতন খবর
            story['seo_story'] = posted[h].get('seo_story', generate_seo_story(story['title'], story['source'], story.get('desc', '')))
            story['img_prompt'] = posted[h].get('img_prompt', generate_image_prompt(story['title'], story['source']))
            story['is_old'] = True
        else:
            # নতুন খবর
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
    """/start কমান্ড হ্যান্ডলার"""
    if str(update.effective_chat.id) != CHAT_ID:
        await update.message.reply_text("⛔ এই বটটি শুধুমাত্র মালিকের জন্য।")
        return
    
    # Agentic AI জেনারেটর ইনিশিয়ালাইজ
    generator = AgenticAIContentGenerator()
    
    await update.message.reply_text(
        "🤖 **Agentic AI নিউজ বট**\n\n"
        "আমি বিশ্বের সেরা টেক মিডিয়া থেকে খবর সংগ্রহ করি এবং সেগুলোকে ফেসবুক-বান্ধব ক্যাপশনে রূপান্তর করি।\n\n"
        "📌 **প্রতিটি পোস্টে থাকছে:**"
        "\n✅ স্ক্রল-স্টপিং হুক"
        "\n✅ ন্যাচারাল ও এনগেজিং বডি"
        "\n✅ বেনিফিট হাইলাইট"
        "\n✅ স্ট্রং CTA"
        "\n✅ ৫-৮টি হ্যাশট্যাগ"
        "\n✅ কমেন্ট উৎসাহিত করার প্রশ্ন"
        "\n\n⏳ খবর আনা হচ্ছে..."
    )
    
    all_stories = get_all_stories()
    
    if not all_stories:
        await update.message.reply_text(
            "📭 কোনো খবর পাওয়া যায়নি।\n\n"
            "🔄 আবার চেষ্টা করুন।"
        )
        return
    
    # নতুন এবং পুরাতন আলাদা
    new_stories = [s for s in all_stories if not s.get('is_old', False)]
    old_stories = [s for s in all_stories if s.get('is_old', False)]
    
    # নতুন খবর
    if new_stories:
        await update.message.reply_text("🆕 **নতুন খবর:**", parse_mode='Markdown')
        for story in new_stories:
            post = generator.generate_full_post(story, is_old=False)
            await update.message.reply_text(post, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    # পুরাতন খবর
    if old_stories:
        await update.message.reply_text("🔄 **পুরাতন খবর (পুনরায়):**", parse_mode='Markdown')
        for story in old_stories:
            post = generator.generate_full_post(story, is_old=True)
            await update.message.reply_text(post, parse_mode='Markdown')
            await asyncio.sleep(0.5)
    
    # সারাংশ
    total = len(all_stories)
    new_count = len(new_stories)
    old_count = len(old_stories)
    
    await update.message.reply_text(
        f"✅ **সফল!** {total}টি খবর পাঠানো হলো!\n"
        f"🆕 নতুন: {new_count}টি\n"
        f"🔄 পুরাতন: {old_count}টি\n\n"
        f"📊 প্রতিটি পোস্ট Agentic AI দ্বারা জেনারেটেড।\n"
        f"💬 আপনার মতামত জানাতে ভুলবেন না!",
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
    
    logger.info("🤖 Agentic AI News Bot চালু হচ্ছে...")
    logger.info("📱 চ্যাট আইডি: {CHAT_ID}")
    logger.info("💡 /start বা /news কমান্ড দিন")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()