#!/usr/bin/env python3
"""Story-First Scripture: annotated English reader, from the public-domain World English Bible.
Full 66-book biblical source; selected passages receive separate narrative summaries.
Source words are not silently rewritten; all additions are identified as editorial notes.
"""
import os, re, sys, time, posixpath, html, collections, urllib.request
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup, NavigableString

SRC_URL = "https://ebible.org/epub/engwebp.epub"
os.makedirs("generated", exist_ok=True)
SRC_FILE = "/tmp/scripture_source.epub"
OUTPUT = "generated/Scripture_Stories_English_Reader_66_Books.epub"

def download():
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(SRC_URL, headers={"User-Agent":"Scripture-Reader/1.0"}), timeout=120) as s:
                data = s.read()
            assert data[:2] == b"PK" and len(data) > 400000, (len(data), data[:40])
            open(SRC_FILE, "wb").write(data)
            print("Downloaded source:", len(data), "bytes", flush=True)
            return
        except Exception as e:
            print("Download attempt", i+1, "failed:", repr(e), flush=True)
            time.sleep(3)
    raise RuntimeError("Could not download public-domain Bible; not generating incomplete content.")

# Each definition: B1 English meaning and, when genuinely hard to explain, Portuguese.
GLOSS = {
"abide":("to stay somewhere or remain in a situation","permanecer"),
"abomination":("something strongly described as wrong or hateful in a religious context","abominação"),
"adversary":("an enemy or someone who is against you","adversário"),
"altar":("a special place where people brought offerings to God","altar"),
"anoint":("to put oil on someone as a sign of being chosen for a special purpose","ungir"),
"apostle":("a person sent out to share Jesus' message","apóstolo"),
"ark":("a large boat, or a sacred chest, depending on the story","arca"),
"atonement":("the repair of a broken relationship with God; making things right","expiação"),
"behold":("look; pay attention to something important",None),
"betray":("to hurt someone's trust by acting against them","trair"),
"blessed":("receiving goodness or favor from God; sometimes meaning deeply fortunate",None),
"bondage":("the state of being controlled or enslaved by someone","escravidão"),
"bountiful":("large in amount; generously given",None),
"captive":("someone held and not free to leave","cativo"),
"cherubim":("heavenly beings described in the Bible","querubins"),
"circumcision":("a physical sign of a covenant in ancient Israel","circuncisão"),
"compassion":("caring about another person's pain and wanting to help","compaixão"),
"condemn":("to judge or declare that someone has done wrong","condenar"),
"congregation":("a group of people gathered to worship","congregação"),
"covenant":("a serious promise or agreement, often between God and people","aliança"),
"disciple":("a follower who learns from a teacher; Jesus had disciples","discípulo"),
"dwelt":("lived or stayed somewhere; past tense of dwell",None),
"endure":("to continue through something difficult without giving up",None),
"eternal":("without an end; lasting forever",None),
"exile":("being forced to live away from your home or country","exílio"),
"faith":("trust in God; choosing to rely on him even without seeing everything",None),
"fasting":("choosing not to eat for a period, often for prayer",None),
"fellowship":("friendship and shared life within a community","comunhão"),
"firstborn":("the child born first in a family","primogênito"),
"flock":("a group of sheep or other animals kept together","rebanho"),
"forgive":("to decide not to hold someone's wrong against them forever",None),
"forsaken":("abandoned or left alone when help was needed","abandonado"),
"fountain":("a place where water comes naturally out of the ground",None),
"gentile":("someone who is not Jewish, in many biblical contexts","gentio"),
"glory":("great beauty, honor, or greatness; often used about God","glória"),
"grace":("kindness and favor that are given freely, not earned","graça"),
"harvest":("the time or action of collecting crops that have grown","colheita"),
"heathen":("an old word for people who do not share a particular religion; can sound insulting today",None),
"heir":("a person who will receive something from family or by promise","herdeiro"),
"holy":("set apart for God; deeply special or morally pure","santo"),
"hosanna":("a shout of praise that originally also meant 'please save us'","hosana"),
"humble":("not acting as if you are better or more important than others",None),
"idol":("an object treated as a god; also something wrongly placed above everything else","ídolo"),
"iniquity":("serious wrongdoing or injustice","iniquidade"),
"inheritance":("something received from a previous generation or by promise","herança"),
"judgment":("a decision about what is right and wrong","julgamento"),
"kingdom":("the land or people ruled by a king; God's reign in many passages","reino"),
"lament":("to express deep sadness or grief","lamentar"),
"leper":("an older term used in translations for a person with a serious skin condition","leproso"),
"levite":("a member of the tribe of Levi, associated with religious duties","levita"),
"manna":("food God provided to Israel in the wilderness, according to Exodus","maná"),
"meek":("gentle and not driven by pride; not necessarily weak","manso"),
"mercy":("kindness shown to someone who needs help or forgiveness","misericórdia"),
"messiah":("the promised person chosen by God; Christians understand this as Jesus","messias"),
"miracle":("an amazing event understood as an act of God's power","milagre"),
"multitude":("a very large group of people","multidão"),
"nation":("a large community of people, often sharing a land or identity","nação"),
"offering":("something given to God as an act of worship","oferta"),
"parable":("a short story that teaches a deeper lesson","parábola"),
"passover":("a Jewish festival remembering Israel's rescue from Egypt","Páscoa judaica"),
"perish":("to die or be destroyed; sometimes used figuratively",None),
"persecute":("to treat someone cruelly because of their beliefs or identity","perseguir"),
"pharisee":("a member of a Jewish religious group in Jesus' time","fariseu"),
"plague":("a serious disease or disaster affecting many people","praga"),
"prophecy":("a message connected with God that may warn, teach, or speak of the future","profecia"),
"prophet":("someone who speaks a message believed to come from God","profeta"),
"psalm":("a sacred song or poem used in worship","salmo"),
"ransom":("a price paid to set someone free","resgate"),
"redeem":("to rescue or buy back; in faith, to bring someone into freedom","redimir"),
"repent":("to recognize wrong actions and turn toward a better way","arrepender-se"),
"resurrection":("coming back to life after death","ressurreição"),
"righteous":("acting in a way that is right and just in God's sight","justo"),
"righteousness":("the quality of being right, fair, and faithful to God","justiça"),
"sabbath":("a weekly day set apart for rest and worship","sábado / dia de descanso"),
"sacrifice":("giving up or offering something important; ancient Israel had ritual sacrifices","sacrifício"),
"salvation":("being rescued; in Christianity, rescue from sin and separation from God","salvação"),
"sanctify":("to make holy or set apart for God's purpose","santificar"),
"scripture":("sacred writing, especially the texts of the Bible","Escritura"),
"serpent":("a snake; sometimes a symbol with a special meaning",None),
"shepherd":("a person who takes care of sheep; also a picture of loving leadership","pastor de ovelhas"),
"sin":("an action or attitude that goes against God's will","pecado"),
"sojourn":("to stay somewhere for a short time, often away from home","habitar temporariamente"),
"steadfast":("strong and faithful, not giving up or changing easily","firme"),
"steward":("a person trusted to take care of something for another person","administrador"),
"synagogue":("a Jewish place of prayer, teaching, and community","sinagoga"),
"tabernacle":("the special portable place of worship used by ancient Israel","tabernáculo"),
"temptation":("the feeling that pushes someone toward doing something they should not do","tentação"),
"testament":("an agreement or covenant; also the name for the Bible's two main parts","testamento"),
"thou":("an old English word meaning 'you' (one person)","tu / você"),
"thee":("an old English word meaning 'you' as the object of a sentence","te / você"),
"thy":("an old English word meaning 'your'","teu / seu"),
"tribulation":("a time of great trouble or suffering","tribulação"),
"transgression":("an act that breaks a rule or moral law","transgressão"),
"vineyard":("a field where grapes are grown","vinhedo"),
"wilderness":("a wild, usually lonely area far from towns","deserto / região selvagem"),
"wisdom":("knowing how to think and act well, not just knowing facts","sabedoria"),
"worship":("to show love, honor, and respect to God","adorar"),
"wrath":("very strong anger, often referring to judgment","ira"),
"yoke":("a wooden tool joining animals for work; sometimes a picture of a burden","jugo")
}

BOOKS = [
("Genesis","GEN","Origins, human choices, family conflict, and promises made to Abraham."),
("Exodus","EXO","A people are rescued from Egypt and learn how to live as a community."),
("Leviticus","LEV","Ancient laws about worship, holiness, and caring for the community."),
("Numbers","NUM","A difficult journey through the wilderness, with trust and doubt."),
("Deuteronomy","DEU","Moses reminds Israel of its story and calls the people to faithfulness."),
("Joshua","JOS","Israel enters the promised land, facing decisions and conflict."),
("Judges","JDG","Repeated failures and new chances in the life of ancient Israel."),
("Ruth","RUT","A gentle story of loyalty, courage, and belonging."),
("1 Samuel","1SA","Samuel, Saul, and David; what makes a good leader?"),
("2 Samuel","2SA","David's reign, including success, mistakes, and consequences."),
("1 Kings","1KI","Solomon and a divided kingdom; leadership and its consequences."),
("2 Kings","2KI","Kings and prophets speak in a time of political and spiritual crisis."),
("1 Chronicles","1CH","Israel's family history and the beginning of David's reign."),
("2 Chronicles","2CH","The kings of Judah and the importance of worship and reform."),
("Ezra","EZR","A community returns from exile and begins to rebuild."),
("Nehemiah","NEH","Rebuilding Jerusalem and rebuilding community trust."),
("Esther","EST","Courage and wise choices in a dangerous political situation."),
("Job","JOB","A difficult conversation about suffering, justice, and faith."),
("Psalms","PSA","Songs and prayers of joy, grief, anger, gratitude, and hope."),
("Proverbs","PRO","Short lessons about wise choices and everyday life."),
("Ecclesiastes","ECC","Honest questions about life's meaning and passing time."),
("Song of Songs","SNG","Poetry about love and longing, with rich symbolic language."),
("Isaiah","ISA","Warnings about injustice and powerful visions of hope."),
("Jeremiah","JER","A prophet speaks to people who resist difficult truths."),
("Lamentations","LAM","Poems of grief after Jerusalem's destruction."),
("Ezekiel","EZK","Striking visions about responsibility, judgment, and renewal."),
("Daniel","DAN","Faithfulness under pressure and symbolic visions of kingdoms."),
("Hosea","HOS","A message about broken loyalty and persistent love."),
("Joel","JOL","A call to return to God and a promise of renewal."),
("Amos","AMO","A strong call for justice and care for vulnerable people."),
("Obadiah","OBA","A short warning against pride and cruelty."),
("Jonah","JON","A reluctant messenger discovers how far mercy can reach."),
("Micah","MIC","Justice, mercy, and humility in public and private life."),
("Nahum","NAM","A poetic message about the fall of an oppressive city."),
("Habakkuk","HAB","A prophet asks why injustice happens and how to keep trusting."),
("Zephaniah","ZEP","Warnings and a vision of future restoration."),
("Haggai","HAG","A community is challenged to rebuild and set priorities."),
("Zechariah","ZEC","Symbolic visions of hope, peace, and restoration."),
("Malachi","MAL","A final prophetic call to honesty and faithfulness."),
("Matthew","MAT","Jesus' life, teachings, death, and resurrection, with strong links to earlier Scripture."),
("Mark","MRK","A fast-moving account of what Jesus did and taught."),
("Luke","LUK","A carefully told account that emphasizes compassion and outsiders."),
("John","JHN","Jesus' identity, signs, conversations, and the meaning of trust."),
("Acts","ACT","How the early Christian movement grew after Jesus' resurrection."),
("Romans","ROM","Paul explains grace, faith, life with God, and life with others."),
("1 Corinthians","1CO","Advice to a divided community learning to love and worship."),
("2 Corinthians","2CO","Paul speaks personally about weakness, courage, and generosity."),
("Galatians","GAL","Freedom, faith, grace, and life shaped by the Spirit."),
("Ephesians","EPH","Unity, grace, and a new way of living together."),
("Philippians","PHP","Joy, humility, and courage during difficulty."),
("Colossians","COL","Jesus' importance and practical changes in daily life."),
("1 Thessalonians","1TH","Encouragement about faith, hope, and perseverance."),
("2 Thessalonians","2TH","A call to patient faithfulness amid confusion."),
("1 Timothy","1TI","Advice for leadership and life in a church community."),
("2 Timothy","2TI","Perseverance, friendship, and passing on what matters."),
("Titus","TIT","Living with integrity and building healthy communities."),
("Philemon","PHM","A short personal letter about reconciliation."),
("Hebrews","HEB","A deep explanation of Jesus using images from Israel's worship."),
("James","JAS","Faith shown through speech, kindness, and practical action."),
("1 Peter","1PE","Hope and good conduct while facing hardship."),
("2 Peter","2PE","Growing in character and staying alert to misleading teaching."),
("1 John","1JN","Love, truth, and living what we believe."),
("2 John","2JN","A brief letter about truth and love."),
("3 John","3JN","A brief letter about friendship and hospitality."),
("Jude","JUD","A warning to defend goodness and treat others with mercy."),
("Revelation","REV","Symbolic visions of conflict, hope, and God's final renewal.")
]
BOOK_BY_NAME = {x[0].lower():x for x in BOOKS}
BOOK_BY_CODE = {x[1].lower():x for x in BOOKS}
# Keep these adaptations separate from the translated biblical text. No invented biblical dialogue.
SCENES = {
("Genesis",1):("The Beginning","Before the world had its familiar shape, the story begins with God. Creation unfolds in stages: light, sky, land, living things, and finally humanity. The repeated message is that creation is good. The chapter ends with a world ready for life."),
("Genesis",3):("A Difficult Choice","In the garden, the man and woman face a choice about trust and obedience. They choose to cross a boundary God has given. When God calls for them, fear and blame appear. The story asks what happens when people turn away from trust."),
("Genesis",12):("The Call","Abram is asked to leave what he knows. He does not receive a map of everything ahead. Instead, he receives a promise and begins a journey. His story starts with trust in the middle of uncertainty."),
("Genesis",37):("Joseph and His Brothers","Joseph is loved by his father, but the tension in his family grows. His brothers become jealous. The chapter begins a long story of loss, surprising changes, and future reconciliation."),
("Exodus",3):("The Burning Bush","Moses notices a bush burning without being destroyed. God calls him by name and speaks about the suffering of Israel. Moses has questions and fears. Yet the call is clear: he must go and help lead the people out."),
("Exodus",14):("A Path Through the Sea","Israel faces the sea ahead and a pursuing army behind. The people are afraid. Moses calls them to trust God. The waters open, and the people cross on dry ground. Their journey toward freedom continues."),
("1 Samuel",17):("David and Goliath","A young shepherd steps forward when experienced soldiers are afraid. David trusts God and refuses to measure courage only by size and strength. His unlikely victory changes how others see him."),
("Psalms",23):("A Shepherd's Care","The writer imagines God as a shepherd who guides, feeds, protects, and stays close. Even in a dark and frightening valley, the speaker is not abandoned. This poem is about trust, not a life without difficulty."),
("Jonah",1):("The Reluctant Messenger","Jonah is asked to bring a warning to Nineveh, but he runs in the opposite direction. His attempt to escape leads to a frightening storm. He learns that avoiding a difficult calling is not so simple."),
("Matthew",5):("A Different Kind of Strength","Jesus sits down to teach. His words challenge ordinary ideas about success: the humble, merciful, and peacemakers matter deeply. He asks his listeners to think beyond appearances and treat people with genuine love."),
("Matthew",6):("What Matters Most","Jesus teaches about generosity, prayer, worry, and trust. He warns against doing good things only to be admired. The chapter invites people to seek God's kingdom instead of letting fear about tomorrow control everything."),
("Matthew",14):("Across the Water","The disciples are on a boat when they see Jesus approaching across the water. They are terrified until he speaks. Peter tries to come toward him but becomes afraid. Jesus helps him, and the disciples respond with wonder."),
("Matthew",28):("An Empty Tomb","Women come to the tomb and learn that Jesus has risen. The disciples are directed to meet him. The Gospel closes not with a simple ending, but with a mission to share what they have learned."),
("Mark",4):("The Storm","Wind and waves threaten the boat. The disciples are frightened while Jesus is sleeping. They wake him, and he commands the storm to be still. Their fear changes into amazement: who is this man?"),
("Luke",15):("The Lost and Found","Jesus tells stories about a lost sheep, a lost coin, and a son who leaves home. In each, being found matters. The final story also asks whether the people who stayed behind can welcome someone back."),
("Luke",24):("Hope Returns","Jesus' followers are confused and grieving. Reports of an empty tomb seem impossible. As the chapter continues, familiar words and unexpected meetings help them understand what has happened."),
("John",3):("A Conversation at Night","Nicodemus, a respected teacher, comes to Jesus with questions. Jesus speaks about being born again and the Spirit. Nicodemus struggles with the language. The conversation moves toward the meaning of God's love."),
("John",4):("At the Well","Jesus speaks with a Samaritan woman by a well. Their conversation moves from ordinary water to deep spiritual questions. She is surprised to be taken seriously, and she shares what she has heard with her community."),
("John",11):("Lazarus","Martha and Mary are grieving because their brother Lazarus has died. Jesus meets their pain with compassion and speaks about life and resurrection. Then he calls Lazarus out of the tomb, leaving those present amazed."),
("John",20):("The Garden and the Room","Mary Magdalene discovers the empty tomb and meets Jesus. Later, his disciples encounter him while gathered together. Thomas has questions, and Jesus meets him with an invitation to believe."),
("Acts",2):("A New Beginning","Jesus' followers gather together. The Holy Spirit comes upon them, and people from different places hear their message. Peter speaks about Jesus, and a new community begins to grow."),
("Acts",9):("A Changed Direction","Saul travels with strong plans to oppose the followers of Jesus. On the road, his life changes. What once seemed certain becomes a new path. Other believers must decide whether to trust the change."),
("Romans",8):("No Longer Alone","Paul explores the difference between a life controlled by fear and one shaped by God's Spirit. He speaks about hope even in suffering and insists that God's love is not easily broken."),
("Revelation",21):("Everything Made New","Near the Bible's ending, John describes a vision of a new heaven and a new earth. The picture centers on God dwelling with people, comfort replacing sorrow, and a renewed creation.")
}
VIDEOS = {
("Matthew",14):("The Chosen: Jesus walks on water — dramatized scene","https://www.youtube.com/watch?v=CXzlIFAcetE"),
("John",3):("The Chosen: Jesus and Nicodemus — dramatized scene","https://www.youtube.com/watch?v=Kb9Ey7_6pMU"),
("John",4):("The Chosen: Conversation with the Samaritan woman","https://www.youtube.com/watch?v=0GDBMnxzrIM"),
("John",11):("The Chosen: Lazarus — dramatized scene","https://www.youtube.com/watch?v=SVmy9KA-0zk")
}

CSS = """
<style type="text/css">
body { font-family: serif; line-height: 1.55; }
a.vocab { text-decoration-line: underline; text-decoration-style: dashed; text-decoration-color: #9c7650; text-underline-offset: .22em; color: inherit; }
.editorial { margin: 1.25em 0; padding: .8em 1em; border-left: 3px solid #b48b5c; background: #faf5ed; color: #382f27; font-family: sans-serif; font-size: .88em; }
.editorial h3 { margin: 0 0 .35em; font-size: 1.1em; }
.editorial p { margin: .4em 0; }
.editorial small { color:#685b4c; }
</style>
"""

def text_to_nodes(soup, text, dest):
    """Link a few glossary words per document without changing original wording."""
    count = collections.Counter()
    pattern = re.compile(r"\b(" + "|".join(re.escape(x) for x in sorted(GLOSS, key=len, reverse=True)) + r")\b", re.I)
    out = []
    pos = 0
    for m in pattern.finditer(text):
        term = m.group(0).lower()
        if count[term] >= 2 or sum(count.values()) >= 100:
            continue
        if m.start() > pos:
            out.append(NavigableString(text[pos:m.start()]))
        tag = soup.new_tag("a", href=dest+"#"+term.replace(" ","-"))
        tag["class"]="vocab"
        tag["title"]="Simple-English meaning in the glossary"
        tag.string=m.group(0)
        out.append(tag)
        count[term]+=1
        pos=m.end()
    if not out:
        return None
    if pos < len(text):
        out.append(NavigableString(text[pos:]))
    return out

def identify(item, soup):
    fn=posixpath.basename(item.file_name).lower()
    hints = (" ".join([item.title or "",fn, " ".join(x.get_text(" ", strip=True)[:100] for x in soup.find_all(re.compile(r"^h[1-4]$"), limit=3))])).lower()
    # Prefer explicit book title in heading or original epub document title
    book = None
    for name,code,desc in BOOKS:
        if re.search(r"(?<![a-z])"+re.escape(name.lower())+r"(?![a-z])",hints):
            book = name; break
    if not book:
        for name,code,desc in BOOKS:
            if re.search(r"(?<![a-z0-9])"+code.lower()+r"(?=\d|[_.-])",fn):
                book=name; break
    chapter=None
    if book:
        n=book.lower()
        matches=[re.search(r"\b"+re.escape(n)+r"\s+(\d{1,3})\b", hints),
                 re.search(re.escape(BOOK_BY_NAME[n][1].lower())+r"[_-]?0*(\d{1,3})(?:\D|$)",fn)]
        for match in matches:
            if match:
                chapter = int(match.group(1)); break
    return book,chapter

def process_doc(item):
    try:
        soup=BeautifulSoup(item.get_content(), "lxml-xml")
        if not soup.find("body"):
            return False, None, None, 0
        book,chapter=identify(item,soup)
        body=soup.find("body")
        total_chars = len(body.get_text(" ",strip=True))
        if total_chars < 200:
            return False,book,chapter,total_chars
        # Annotate terms without altering biblical wording.
        link = posixpath.relpath("reader-glossary.xhtml", posixpath.dirname(item.file_name) or ".")
        changed=0
        for t in list(body.find_all(string=True)):
            if not isinstance(t,NavigableString) or not t.strip() or not t.parent:
                continue
            if t.parent.name in ("a","title","style","script","h1","h2","h3","h4","sup","small"):
                continue
            if t.find_parent(["a","nav","svg"]): continue
            nodes=text_to_nodes(soup,str(t),link)
            if nodes:
                t.replace_with(*nodes)
                changed+=1
        # Only add literary scene if chapter identity is unambiguous.
        if (book,chapter) in SCENES:
            title,story=SCENES[(book,chapter)]
            note=soup.new_tag("aside")
            note["class"]="editorial"
            h=soup.new_tag("h3");h.string="Before you read: "+title;note.append(h)
            p=soup.new_tag("p");p.string=story;note.append(p)
            small=soup.new_tag("small");small.string="Literary recap, not a Bible verse or a quotation."
            note.append(small)
            if (book,chapter) in VIDEOS:
                vtitle,url=VIDEOS[(book,chapter)]
                p2=soup.new_tag("p");p2.string="Watch in English: "
                a=soup.new_tag("a",href=url);a.string=vtitle
                p2.append(a);note.append(p2)
                caution=soup.new_tag("small");caution.string="Video dramatization may include fictional details not stated in Scripture."
                note.append(caution)
            body.insert(0,note)
        head=soup.find("head")
        if head:
            sty=BeautifulSoup(CSS,"lxml-xml")
            for c in list(sty.contents):
                head.append(c)
        item.set_content(str(soup).encode("utf-8"))
        return True,book,chapter,total_chars
    except Exception as e:
        print("SKIP PROCESS",item.file_name,repr(e),flush=True)
        return False,None,None,0

def ebook_page(title, file, content):
    return epub.EpubHtml(title=title,file_name=file,lang="en",content=content)

def guide():
    body="""<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Start here</title>
<style>body{font-family:sans-serif;line-height:1.6;color:#252323}h1{color:#77532f}h2{color:#84603b}p{margin:.8em 0}.note{border-left:3px solid #ad8755;padding:.3em 1em;background:#f8f3ea}</style>
</head><body>
<h1>Scripture Stories</h1><h2>A Story-First English Reader</h2>
<p><strong>Read the whole Bible. Learn English. Ask honest questions.</strong></p>
<p>This ebook includes the full 66-book Protestant canon as the original English text of the public-domain World English Bible Protestant edition, with added learning features.</p>
<p><strong>Editorial distinction:</strong> Bible verses are from the source translation and have <em>not</em> been rewritten into a new translation. Added narrative recaps, book introductions, links and dictionary meanings are teaching material, not Scripture. This edition is not published or endorsed by eBible.org.</p>
<h2>How to use this edition</h2><p>Read a little at a time. Dotted/dashed-underlined words link to a friendly English dictionary at the back. Use your reader's Back button to return to the page. Some difficult terms also have Portuguese help.</p>
<p>In selected chapters, a <strong>Before you read</strong> box introduces a Bible scene in accessible narrative English. These summaries are clearly marked and do not replace the source text.</p>
<h2>Start with Jesus</h2><p>If the Bible feels hard, begin with Mark, then Luke, John, and Matthew. After that, Genesis, Exodus, the Psalms, and Acts can be a good route. You do not have to finish it quickly.</p>
<h2>Read with curiosity, not fear</h2><p>Try these questions: What happened? What does this show about people? What might this show about God? What is still confusing?</p>
<div class="note"><p><strong>Videos:</strong> Selected chapters contain direct YouTube links to scenes from <em>The Chosen</em>. The series is a creative dramatization, not a replacement for biblical text. Internet access is required to watch them. Availability and audio language may vary.</p></div>
<p><strong>Source and rights:</strong> Bible source: World English Bible, Protestant edition (66 books), public domain: https://ebible.org/details.php?id=engwebp . The name 'World English Bible' is the source attribution, not the name of this edited edition.</p>
<p><a href="reader-book-guide.xhtml">Explore the 66 book guide</a> | <a href="reader-glossary.xhtml">Open the English dictionary</a></p></body></html>"""
    return ebook_page("Start Here","reader-start.xhtml",body)

def book_guide():
    parts=['<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Book guide</title><style>body{font-family:sans-serif;line-height:1.6} h1{color:#77532f} h2{color:#77532f} li{margin:.4em 0}</style></head><body>',
    '<h1>The 66 books at a glance</h1><p>These are editorial introductions, not Bible verses. Use the ebook table of contents to open the biblical books.</p><h2>Old Testament</h2><ol>']
    for idx,(name,code,desc) in enumerate(BOOKS):
        if idx==39: parts.append('</ol><h2>New Testament</h2><ol>')
        parts.append('<li><strong>'+html.escape(name)+'</strong> — '+html.escape(desc)+'</li>')
    parts.append('</ol></body></html>')
    return ebook_page("Guide to All 66 Books","reader-book-guide.xhtml","".join(parts))

def glossary_page():
    parts=["""<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Simple English Dictionary</title>
<style>body{font-family:sans-serif;line-height:1.6}h1{color:#77532f}dt{font-weight:bold;margin-top:1em;color:#664727}dd{margin-left:.4em}.pt{font-size:.85em;color:#78654f}</style></head><body>
<h1>Simple English Dictionary</h1><p>Tap your reader's Back button to return to where you were reading. Definitions are short and designed for English learners. Portuguese is included only where especially useful.</p><dl>"""]
    for term,(definition,pt) in sorted(GLOSS.items()):
        parts.append('<dt id="'+term+'">'+html.escape(term.title())+'</dt>')
        parts.append('<dd>'+html.escape(definition)+ (('<p class="pt">Português: '+html.escape(pt)+'</p>') if pt else '') +'</dd>')
    parts.append("</dl></body></html>")
    return ebook_page("Simple English Dictionary","reader-glossary.xhtml","".join(parts))

def main():
    download()
    book=epub.read_epub(SRC_FILE,options={"ignore_ncx":False})
    books_found=collections.Counter()
    found_scenes=[]
    processed=0; total_docs=0
    for item in list(book.get_items_of_type(ITEM_DOCUMENT)):
        total_docs+=1
        if ("nav" in item.file_name.lower() or "toc" in item.file_name.lower()) and len(item.get_content()) < 30000:
            continue
        ok,b,ch,chars=process_doc(item)
        if ok:
            processed+=1
            if b: books_found[b]+=1
            if (b,ch) in SCENES: found_scenes.append((b,ch))
        if total_docs<=12:
            print("SAMPLE",item.file_name,repr(item.title),b,ch,chars,flush=True)
    print("EPUB original doc count",total_docs,"annotated documents",processed,flush=True)
    print("Recognized books",len(books_found),repr(books_found.most_common(70)),flush=True)
    print("Recognized narrative chapters",len(found_scenes),repr(found_scenes),flush=True)
    if processed < 66:
        raise RuntimeError("Too few Scripture documents annotated. Review source document structure.")
    intro=guide();overview=book_guide();words=glossary_page()
    for item in (intro,overview,words):
        book.add_item(item)
    oldspine=list(book.spine)
    # Preserve the original source reading order, and add original teaching pages.
    book.spine = [oldspine[0]]+[intro,overview]+oldspine[1:]+[words] if oldspine and oldspine[0]=='nav' else [intro,overview]+oldspine+[words]
    book.toc = tuple([epub.Link(intro.file_name,intro.title,"reader-intro"),
                      epub.Link(overview.file_name,overview.title,"reader-books")]+list(book.toc)+[
                      epub.Link(words.file_name,words.title,"reader-gloss")])
    book.set_title("Scripture Stories: A Story-First English Reader")
    book.set_language("en")
    # Original text is WEB Protestant; editorial content separately credited.
    book.add_metadata("DC","description","66-book Bible reading edition with clear editorial narrative guides, dashed vocabulary links, simple English glossary and selected external videos.")
    epub.write_epub(OUTPUT,book,{"epub3_pages":False})
    size=os.path.getsize(OUTPUT)
    print("CREATED",OUTPUT,"bytes",size,flush=True)
    if size < 400000: raise RuntimeError("EPUB unexpectedly small; likely missing source contents.")
    # Round-trip check and inspect internal references.
    test=epub.read_epub(OUTPUT)
    docs=list(test.get_items_of_type(ITEM_DOCUMENT))
    names={it.file_name for it in docs}
    assert "reader-glossary.xhtml" in names and "reader-start.xhtml" in names
    assert len(docs) >= total_docs
    print("VALIDATED document count",len(docs),"size",size,flush=True)
if __name__=="__main__":
    main()
