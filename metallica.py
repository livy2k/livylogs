import json

# Master dataset of 50 Metallica songs with Uncle Rico style trivia and tabs
metallica_dataset = [
    {
        "song_title": "Hit the Lights",
        "album": "Kill 'Em All",
        "trivia": "Man, back in '83, James and Lars were throwing down this track like it was nothing. I bet if I was in the studio back then, we would’ve gone multi-platinum in a week. No doubt. No doubt in my mind. This riff is faster than a steak tossing competition, back when I could throw a pigskin a quarter mile.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------9-------------7-----5---|\nA|---------7-------------5-----3---|\nE|-0-0-0-0---0-0-0-0-0-0---0-0-----|"
        }
    },
    {
        "song_title": "The Four Horsemen",
        "album": "Kill 'Em All",
        "trivia": "Dave Mustaine wrote the original version, but the boys spiced it up. You know, if Coach had put me in the band back then, we would've won State with this riff alone. It’s got that triplets gallop, man. I used to gallop on my bike just like that back in '82. Pure power.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|-----------------------------------|\nB|-----------------------------------|\nG|-----------------------------------|\nD|-----------------------------------|\nA|---7---5-7---5-7---5-7-5-----------|\nE|-0---0-----0-----0-------7-6-5-3---| "
        }
    },
    {
        "song_title": "Motorbreath",
        "album": "Kill 'Em All",
        "trivia": "This is the only track credited solely to Hetfield on the debut album. Talk about carrying the team. Reminds me of the '82 season. If the coach just handed me the ball, we’d be holding the trophy right now. This riff is just pure, unadulterated speed, like my fastball used to be.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|-----------------------------------|\nB|-----------------------------------|\nG|-----------------------------------|\nD|-9-9-9-12--7-7-7-10--5-5-5-8--7-7--|\nA|-7-7-7-10--5-5-5-8---3-3-3-6--5-5--|\nE|-----------------------------------|"
        }
    },
    {
        "song_title": "Jump in the Fire",
        "album": "Kill 'Em All",
        "trivia": "This one has a real funky, swinging metal groove to it. Kirk Hammett had to learn this right after joining the band. I tell ya, if I had a time machine, I'd go back to '83 and show Kirk how to really bend those strings. I could bend a crowbar with my bare hands back then.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|-------3-----5---3---------------|\nA|---3-5---5-3---5---5-3-----------|\nE|-5---------------------5-3-0-----|"
        }
    },
    {
        "song_title": "Whiplash",
        "album": "Kill 'Em All",
        "trivia": "The ultimate thrash anthem, man. It's just a non-stop down-picked E-string assault. It makes your neck sore just listening to it. I used to have a neck like a bull back when I was throwing touchdowns over those mountains. They don't make 'em like us anymore.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|---------7-7-7---------7-7-5-----|\nE|-0-0-0-0-------0-0-0-0-------7---|"
        }
    },
    {
        "song_title": "Phantom Lord",
        "album": "Kill 'Em All",
        "trivia": "This track starts out real sneaky with that clean intro before blasting your face off with a heavy riff. It's got a lot of heart, kind of like my high school football career before things went south. If things had gone differently, I’d be soaking it up in a hot tub with a model right now.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|-----9-----7-----9-----10--9-----|\nA|-----7-----5-----7-----8---7-----|\nE|-0-0---0-0---0-0---0-0-----------|"
        }
    },
    {
        "song_title": "No Remorse",
        "album": "Kill 'Em All",
        "trivia": "A song about going to war and leaving nothing behind. It starts with a chunky riff that just chugs along. Reminds me of how I used to plow right through the defensive line back in the day. No remorse, just pure physical dominance. I bet I could still do it.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------5-----------|\nA|-7---5---7---5---7---3---5---5---|\nE|-5-0-3-0-5-0-3-0-5-0-----3-0-3---| "
        }
    },
    {
        "song_title": "Seek & Destroy",
        "album": "Kill 'Em All",
        "trivia": "Oh, man. This riff right here is a masterpiece. Written in a garage, but it sounds like it belongs in a stadium. You know, if I was playing guitar on this track, people would still be talking about it today. Over those mountains, man. That riff just searches and destroys, just like me on a Friday night in '82.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|-----------------------------------|\nB|-----------------------------------|\nG|-------7-5-------------------------|\nD|-----------7-6-5-----5-------------|\nA|---0-0-----------7-6---7-----------|\nE|--------------------------0--0-----|"
        }
    },
    {
        "song_title": "Metal Militia",
        "album": "Kill 'Em All",
        "trivia": "This is the fastest track on the whole debut, man. It closes out the album like a freight train. If I had been running the merch table for them back then, we’d be millionaires twice over by now. Seriously. You just down-pick like your life depends on it.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|---------7\5---------5/7---------|\nE|-0-0-0-0-5\3-0-0-0-0-3/5---------|"
        }
    },
    {
        "song_title": "Fight Fire with Fire",
        "album": "Ride the Lightning",
        "trivia": "Starts off all pretty with an acoustic guitar, then BOOM! It hits you like a sack of potatoes. It’s about nuclear war. Heck, back in high school, my right arm was considered a lethal weapon. I could've generated enough horsepower to rival this riff, easily.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|-----2-----3-----2-----5---4-----|\nE|-0-0-0-0-0-1-0-0-0-0-0-3-0-2-----|"
        }
    },
    {
        "song_title": "Ride the Lightning",
        "album": "Ride the Lightning",
        "trivia": "The title track, man. It’s got that progressive, heavy feel. They recorded this in Denmark because it was cheaper. Dang web of life, always trying to save a buck. If I had the royalties from this riff, I’d be living in a mansion, eating prime rib every single night.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------4-----------|\nA|-----4-5---4-5---4-5-2-5-4-5-----|\nE|-2-2-----2-----2-------3-2-3-----|"
        }
    },
    {
        "song_title": "For Whom the Bell Tolls",
        "album": "Ride the Lightning",
        "trivia": "Cliff Burton played the intro on a bass with a wah-wah pedal, making it sound like a guitar. Pretty clever, but honestly, I used to do wilder stuff with a regular old stereo back in my van. This chromatic riff is heavy enough to knock a scout right out of his bleacher seat.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------9---8---7---6-----------|\nA|-2-------7---6---5---4---2-------|\nE|-0-0-0-0-----------------0-------|"
        }
    },
    {
        "song_title": "Fade to Black",
        "album": "Ride the Lightning",
        "trivia": "Their first big ballad. People called them sellouts, but that’s just because they didn't understand the depth, man. It’s like when I tell people I could’ve played in the pros. They just don't get it. This acoustic riff is deeper than the valley behind my trailer.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------0---------------2--------|\nB|----------1-----------3---3------|\nG|------2-----2-------2-------2----|\nD|----2---------2---4-----------4--|\nA|--0-------------2----------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Trapped Under Ice",
        "album": "Ride the Lightning",
        "trivia": "This riff is fast and cold, based on a track Kirk brought over from his old band, Exodus. I know a thing or two about being trapped, mostly by the passing of time and bad coaching decisions. If they let me play the solo on this, it would’ve melted the ice instantly.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
import json

# Secondary dataset of 30 additional Metallica songs with Uncle Rico style trivia and tabs
metallica_dataset_part2 = [
    {
        "song_title": "Anesthesia (Pulling Teeth)",
        "album": "Kill 'Em All",
        "trivia": "Cliff Burton's legendary bass solo, man. Just him, a distortion pedal, and Lars ticking along. Honestly, if I had a wah pedal on my voice when I talked to those football scouts, they would’ve been mesmerized. No doubt. This riff is all about shredding on four strings.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|--------14-12-11-----------------|\nD|--12-14----------14-12-11--------|\nA|---------------------------14----|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "The Thing That Should Not Be",
        "album": "Master of Puppets",
        "trivia": "They tuned down to D Standard for this one to sound like a giant sea monster. Lower than a snake's belly. If I had tuned my sound system that low in '82, I would've shook the loose tiles right off the high school gym ceiling during the homecoming dance. Total power.",
        "main_riff_tab": {
            "tuning": "D Standard (D G C F A D)",
            "notation": "D|---------------------------------|\nA|---------------------------------|\nF|---------------------------------|\nC|---------------------------------|\nG|-----1---------2---------3---2---|\nD|-0-0---0-0-3-0---0-0-4-0---0-----|"
        }
    },
    {
        "song_title": "Escape",
        "album": "Ride the Lightning",
        "trivia": "The band claims they wrote this in a rush just because the record label demanded a catchy radio song. Talk about pressure from management. Reminds me of when Coach told me to change my throwing mechanics in the 4th quarter. If I had escaped his terrible system, we would've won State.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--4--4-------2--2----------------|\nA|--2--2--5-5--0--0--2--2----------|\nE|--------3-3--------0--0----------|"
        }
    },
    {
        "song_title": "The God That Failed",
        "album": "Metallica (The Black Album)",
        "trivia": "Starts out with that heavy, isolated bass line. James wrote it about a real personal tragedy. It’s got a slow, bitter march to it. Reminds me of the tragic oversight by the local sports press back in my prime. They just completely failed to see a legend in their midst.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|------2---3---2-------5---4------|\nE|--0-0---0---0---0-0-0---0--------|"
        }
    },
    {
        "song_title": "The Outlaw Torn",
        "album": "Load",
        "trivia": "A massive ten-minute jam with a giant orchestral swell at the end. They actually had to cut the song short on the CD version because it didn't fit. I know exactly how that feels, man. My immense physical talents were just too big for this small town to handle.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|--2------5/7--5--2---------------|\nE|--0--3-5---------0--3-5-3-2------|"
        }
    },
    {
        "song_title": "Hero of the Day",
        "album": "Load",
        "trivia": "This one has a real soft, melodic verse before it kicks into a heavy rock chorus. It’s about everyday heroes. Heck, if the town council just looked at my old high school tapes, they'd realize the true hero of this valley has been living in a van right under their noses.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------2---------------3--------|\nB|------3---3-----------3---3------|\nG|----2-------2-------0-------0----|\nD|--0---------------0--------------|\nA|---------------------------------|\nE|----------------3----------------|"
        }
    },
    {
        "song_title": "Devil's Dance",
        "album": "Reload",
        "trivia": "A slow, grinding riff that sounds like it’s pulling you down into a swamp. It relies on massive, heavy pitch-bends on the bass. I used to do a dance like this on the field, totally faking out the safety before dropping a 60-yard dime into the endzone. Unstoppable.",
        "main_riff_tab": {
            "tuning": "D Standard (D G C F A D)",
            "notation": "D|---------------------------------|\nA|---------------------------------|\nF|---------------------------------|\nC|---------------------------------|\nG|--0-0--3-5--0-0-3-5--6~----------|\nD|--0-0--1-3--0-0-1-3--4~----------|"
        }
    },
    {
        "song_title": "The Unforgiven II",
        "album": "Reload",
        "trivia": "The sequel to their legendary ballad, using a B-Bender guitar to get a country-western twang in the intro. Pretty slick. If I had a time machine, I'd go back to '97 and show James how to really wear a cowboy hat. I've got the rugged look down perfectly, no lie.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|------2--------0-----------------|\nD|----2--------2----------3-----2--|\nA|--0------2-3----------3-----2----|\nE|--------------------1-----0------|"
        }
    },
    {
        "song_title": "Turn the Page",
        "album": "Garage Inc.",
        "trivia": "A Bob Seger cover about the exhausting grind of being a musician on the road. Man, living in trucks and hotels, staring at the highway... that is a page I turn every single day in the sales game. If Bob Seger saw my hustle, he'd write a sequel about me.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------0---------------0--------|\nB|------3---3-----------3---3------|\nG|----2-------2-------2-------2----|\nD|--0-----------0------------------|\nA|------------------3-----------3--|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Whiskey in the Jar",
        "album": "Garage Inc.",
        "trivia": "An old Irish folk song they turned into a massive rock anthem. Won them a Grammy, too. I used to drink a little whiskey out of a jar back in the summer of '82 after throwing touchdowns. If I was in Ireland back then, they probably would’ve made me king.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------5-5---------------------|\nA|--2-2----3-3----5-5----2-2-------|\nE|--0-0-----------3-3----0-0-------|"
        }
    },
    {
        "song_title": "Die, Die My Darling",
        "album": "Garage Inc.",
        "trivia": "A Misfits cover that they beefed up with massive, crushing guitar tracks. It’s just pure punk-rock energy with metal production. Reminds me of my old workout routine before the bad luck hit. Just aggressive, non-stop physical output. No stopping me back then.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--6-6-6-6-----------4-4-4-4------|\nA|--4-4-4-4--7-7-7-7--2-2-2-2------|\nE|-----------5-5-5-5---------------|"
        }
    },
    {
        "song_title": "Am I Evil?",
        "album": "Garage Inc.",
        "trivia": "Originally by Diamond Head, this is the song that practically invented the Metallica style. That heavy chromatic march is iconic. If my high school team had marched out to this riff, the other guys would’ve forfeited before kickoff. They would’ve been too intimidated by my presence.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|--2--------------5--4--3---------|\nE|--0--0-0-0-0-0-0-3--2--1---------|"
        }
    },
    {
        "song_title": "I Disappear",
        "album": "Mission: Impossible 2 OST",
        "trivia": "Famous for being the song that leaked on Napster, sparking the massive digital music war. Talk about a mess. If somebody had leaked my high school game footage onto the internet back then, the NFL would've signed me on the spot. I would've been a millionaire overnight.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------2---------------2-------|\nA|---------2---------------2-------|\nE|--0-3-5----3-0----0-3-5----5-3---| "
        }
    },
    {
        "song_title": "Some Kind of Monster",
        "album": "St. Anger",
        "trivia": "The title track for their documentary. The main riff is a heavily down-tuned, looping pattern that sounds like a big engine idling. Reminds me of my custom van when I’ve got the heat blasting in the winter. Just a pure beast waiting to be unleashed.",
        "main_riff_tab": {
            "tuning": "Drop C (C G C F A D)",
import json

# Master dataset of 50 Megadeth songs with Uncle Rico style trivia and tabs
megadeth_dataset = [
    {
        "song_title": "Mechanix",
        "album": "Killing Is My Business... and Business Is Good!",
        "trivia": "Dave Mustaine wrote this blistering track before getting kicked out of his old squad. He plays it twice as fast out of pure spite. Man, I know all about getting slighted by management. If Coach had let me call the plays back in '82 instead of benching me, we'd have taken State by 40 points. No doubt in my mind.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--------7-----9-----7---10\\9-7---|\nA|--------5-----7-----5----8\\7-5---|\nE|--0-0-0---0-0---0-0---0----------|"
        }
    },
    {
        "song_title": "Rattlehead",
        "album": "Killing Is My Business... and Business Is Good!",
        "trivia": "This track is just a non-stop headbanging anthem, introducing their mascot Vic Rattlehead. Mustaine shreds so hard his fingers are practically a blur. I used to have that exact kind of blistering hand speed when spinning spirals downfield. If the scouts were watching me headbang to this in my van, they'd sign me instantly.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--9\\8-----8\\7-----7\\6------------|\nA|--7\\6-0-0-6\\5-0-0-5\\4-0-0-5-4-3--|\nE|--------------------------3-2-1--|"
        }
    },
    {
        "song_title": "Killing Is My Business... and Business Is Good!",
        "album": "Killing Is My Business... and Business Is Good!",
        "trivia": "A song about a high-paid sniper doing his job. Pure professional dominance. It's got this jagged, bouncing riff that requires perfect physical execution. Reminds me of my accuracy from 60 yards out. Give me a pigskin and a clear target, and I'll drop it in their bucket every single time. Business is always good when I'm on the field.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------5---7p5-----|\nA|--7--5h7---5h7-5---5---7-----7---|\nE|--0------7-------7---------------|"
        }
    },
    {
        "song_title": "Loved to Deth",
        "album": "Killing Is My Business... and Business Is Good!",
        "trivia": "The very first track on their debut album, featuring a crazy complex thrash arrangement. Mustaine wrote it about a girl who didn't love him back. Dang web of life, man. Girls used to swoon when I threw touchdowns back in high school. If I could go back to '82, I'd write a ballad that would secure my romantic legacy forever.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--9---------10---------12--------|\nA|--7---------8----------10--------|\nE|----0-0-0-0----0-0-0-0----0-0-0-0|"
        }
    },
    {
        "song_title": "The Skull Beneath the Skin",
        "album": "Killing Is My Business... and Business Is Good!",
        "trivia": "This track details the creation of Vic Rattlehead. It's got a creeping, sinister chromatic buildup. Honestly, my physical form back in the day was so shredded it was practically supernatural. If the local sports doctors had examined my throwing arm, they would've thought it was made of reinforced steel.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|------5---4---3---2---1----------|\nE|--0-0---0---0---0---0---3-2-1----|"
        }
    },
    {
        "song_title": "Peace Sells",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "That opening bass line is so iconic it was used on MTV News for years. But who's buying? Not me, man. If I had been paid royalties for every time someone played a sick groove in my vicinity, I'd be soaking in a hot tub with a model right now. Instead, I'm stuck pitching premium kitchenware out of my vehicle.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|-----------------7-----5---------|\nA|-----5p4---5-----------5h7-------|\nE|--7------7---5-5---5-5-----0-----|"
        }
    },
    {
        "song_title": "Wake Up Dead",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "A song about a guy sneaking into his own house so his lady doesn't find out he's been misbehaving. It’s got about four different incredible riffs chained together. I used to sneak past my coach's curfew all the time back in '82 just to hang out with the cheerleaders. I had smooth moves on and off the field, no lie.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|------------------5--------------|\nA|--7---------------3--5--2--------|\nE|--0-0-0-0-0-0-0-0----3--0--------|"
        }
    },
    {
        "song_title": "The Conjuring",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "Mustaine claims this song contains actual ritualistic hexes in the lyrics. Real dark magic, man. Speaking of magic, you should’ve seen the way I could make a defensive line disappear with a single play-action fake. It was straight up wizardry. They couldn't stop me.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--------8\\7-------7\\5------------|\nA|--------6\\5-------5\\3-----5/7----|\nE|--0-0-0-----0-0-0-----0-0-3/5----|"
        }
    },
    {
        "song_title": "Devils Island",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "About a prisoner trapped on an island waiting for execution. The galloping riff simulates the sheer panic of trying to break out. I know a thing or two about being trapped by historical circumstances and short-sighted coaching staffs. If they just let me open up the offense, we'd have broken out of this valley years ago.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|------9-----9-----9--------------|\nA|------7-----7-----7------5-4-----|\nE|--0-0---0-0---0-0----3-2-----5---|"
        }
    },
    {
        "song_title": "Good Mourning/Black Friday",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "A massive, chaotic track that starts with an acoustic intro before turning into a total slasher film of a thrash song. It's completely relentless. Reminds me of my training sessions under the hot August sun back in high school. I was a physical machine, crushing anyone who lined up across from me.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------4-------------5---------|\nA|---------2-------------3---------|\nE|--0-0-0-0---0-0-0-0-0-0---0-0----|"
        }
    },
    {
        "song_title": "Bad Omen",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "A progressive track with weird time signatures and complex backing arrangements. A real bad omen for anyone trying to play rhythm along with it. The only bad omen I ever faced was seeing our starting fullback fumble on the one-yard line in the biggest game of our lives. Ruined my legacy, man.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--9-----7/9----------------------|\nA|--7-7-7-5/7-7-7--5-4-3-----------|\nE|-----------------3-2-1-----------|"
        }
    },
    {
        "song_title": "My Last Words",
        "album": "Peace Sells... But Who's Buying?",
        "trivia": "A song about playing Russian roulette, featuring one of Mustaine's greatest guitar solos ever. The ending riff just fast-gallops into oblivion. If my high school football career had a dramatic climax like this track, Hollywood would've bought the film rights by now. I'd be played by a real handsome actor.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------5-----|\nA|--2-2-2-2-2-2-2-2-2-2-2-2--3--5--|\nE|--0-0-0-0-0-0-0-0-0-0-0-0-----3--|"
        }
    },
    {
        "song_title": "Set the World Afire",
        "album": "So Far, So Good... So What!",
        "trivia": "This was the very first song Dave Mustaine wrote immediately after leaving his former band, penned on a survival leaflet while riding a bus home. Talk about motivation. If I had written down my sports strategies on a napkin back in '82, it would've revolutionized the game. This riff absolutely roars.",
        "main_riff_tab": {
import json

# Master dataset of 50 Ozzy Osbourne / Black Sabbath tracks with Uncle Rico style trivia and tabs
ozzy_sabbath_dataset = [
    {
        "song_title": "Black Sabbath",
        "album": "Black Sabbath",
        "trivia": "Tony Iommi down-tuned his strings and played that eerie tritone devil's interval because his fingertips were chopped off in a factory. Talk about playing through the pain. Reminds me of when I played the entire second half of the '82 semi-finals with a hangnail that would've hospitalized a lesser man. Pure mental toughness.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------3-----------------------|\nA|-----5-------4~------------------|\nE|--3------------------------------|"
        }
    },
    {
        "song_title": "N.I.B.",
        "album": "Black Sabbath",
        "trivia": "Geezer Butler starts this off with a distorted bass solo that sounds like a spaceship landing. The title is just a nickname for Bill Ward's beard, but people thought it meant Lucifer. Heck, people think I'm a myth when they hear about my 80-yard passes. If I had Geezer's distortion pedal hooked up to my van's horn, I'd clear out traffic on the highway in seconds.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--------7-9-7--------------------|\nA|--7-9---------9-8-7---5----------|\nE|------------------------7--------|"
        }
    },
    {
        "song_title": "The Wizard",
        "album": "Black Sabbath",
        "trivia": "Ozzy blows a mean harmonica on this track, matching Tony's heavy blues riff perfectly. Inspired by Gandalf from Lord of the Rings. I'm a bit of a wizard myself when it comes to predicting exactly where the safety is going to cheat over. If Coach had just trusted my magic, we'd be living out of golden mansions right now instead of trailers.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|--5--5-5--3--2-----2--5--3-------|\nE|----------------3----------------|"
        }
    },
    {
        "song_title": "Paranoid",
        "album": "Paranoid",
        "trivia": "They wrote and recorded this entire track in about 20 minutes because the album was too short. 20 minutes! I can pitch three sets of durable food containers and clear a quarter mile on foot in that time, easy. This simple E-minor chug became a global anthem because it’s pure, unfiltered energy, much like my arm talent.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|-----------7-9-7-----------------|\nD|--9-9--7-9-------9-7-------------|\nA|--7-7----------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Iron Man",
        "album": "Paranoid",
        "trivia": "Tony Iommi came up with this riff, and Ozzy said it sounded like a big iron bloke walking around. It’s got that heavy, synchronized bend. I used to be called the Iron Man of the valley back before my bad luck started acting up. If a scout saw me tracking downfield to this rhythm, they'd have written a blank check on the spot.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|-----5---5/7-7---10\\9-10\\9-10\\5-5|\nA|--2--3---3/5-5----8\\7--8\\7--8\\3-3|\nE|--0------------------------------|"
        }
    },
    {
        "song_title": "War Pigs",
        "album": "Paranoid",
        "trivia": "An absolute anti-war epic that starts with an air-raid siren. It leaves a giant gap after the chord for Ozzy to sing. Talk about spatial awareness. I used to leave defenders stranded in giant gaps like that back in the fall of '82. No doubt. No doubt in my mind. Just columns of empty space behind me.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--9-----9/12--11\\9---------------|\nA|--7-----7/10---9\\7---7p5---------|\nE|----0-0------------------7-------|"
        }
    },
    {
        "song_title": "Fairies Wear Boots",
        "album": "Paranoid",
        "trivia": "Ozzy wrote the lyrics after getting into a brawl with a bunch of skinheads in boots. It’s got a real groovy, swing-style heavy metal riff. I can handle myself in a scrap, too, especially if someone questions my synthetic fiber merchandise. One solid right hook and they’d be seeing fairies for a week, no lie.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|--------3-5-5b7-5-3--------------|\nD|----3-5-------------5-3----------|\nA|--5---------------------5--------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Electric Funeral",
        "album": "Paranoid",
        "trivia": "Tony uses a heavy wah-wah pedal effect on this riff to make it sound like a literal apocalypse. It’s real sludgy and dark. I felt like I was attending my own electric funeral when Coach benched me in the final quarter of the championship game. A total devastation of sports history. Riff kills, though.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|------9-9--8-8--7-7--6/7---------|\nD|------9-9--8-8--7-7--6/7---------|\nA|--7-7----------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Sweet Leaf",
        "album": "Master of Reality",
        "trivia": "Starts out with Ozzy coughing his lungs out after taking a drag from a cigarette, which they looped in the studio. Then it hits you with a riff so heavy it'll rattle your teeth. I used to clear my throat just like that before stepping up to the microphone at the regional athletic banquets. Pure confidence.",
        "main_riff_tab": {
            "tuning": "1.5 Steps Down (C# F# B E G# C#)",
            "notation": "C#|---------------------------------|\nG#|---------------------------------|\nE |---------------------------------|\nB |---------------------5---7-------|\nF#|--7--7---5--6--7-----3---5-------|\nC#|--5--5---3--4--5-----------------|"
        }
    },
    {
        "song_title": "Children of the Grave",
        "album": "Master of Reality",
        "trivia": "A relentless driving gallop that practically created the blueprint for thrash metal rhythm tracking. Bill Ward's percussion handles the heavy lifting here. I used to gallop over the defensive line with that exact same forward momentum. If the scouts saw my leg drive to this beat, they’d be hyperventilating.",
        "main_riff_tab": {
            "tuning": "1.5 Steps Down (C# F# B E G# C#)",
            "notation": "C#|---------------------------------|\nG#|---------------------------------|\nE |---------------------------------|\nB |---------------------------------|\nF#|--4-4-4-4-4-4-4-4-4-4-4-4-7-6----|\nC#|--2-2-2-2-2-2-2-2-2-2-2-2-5-4----|"
        }
    },
    {
        "song_title": "Into the Void",
        "album": "Master of Reality",
        "trivia": "James Hetfield’s favorite Black Sabbath song. It features a slow, mechanical descent into a heavy groove that feels like entering outer space. Speaking of the void, that’s exactly where my career went when the system failed me. But this riff is pure engineering genius. I respect the hustle.",
        "main_riff_tab": {
            "tuning": "1.5 Steps Down (C# F# B E G# C#)",
            "notation": "C#|---------------------------------|\nG#|---------------------------------|\nE |---------------------------------|\nB |---------------------------------|\nF#|-------5-4-3---------------------|\nC#|--0--7--------7-6-5-3b-0---------|"
        }
    },
    {
        "song_title": "Lord of This World",
        "album": "Master of Reality",
        "trivia": "Deals with the internal rot of humanity over a sluggish, bluesy stomp that punches you right in the gut. I was practically the lord of this world back in high school. When I walked down the hallways, people moved aside out of pure reverence. If things went differently, I’d be running a corporate franchise right now.",
        "main_riff_tab": {
            "tuning": "1.5 Steps Down (C# F# B E G# C#)",
            "notation": "C#|---------------------------------|\nG#|---------------------------------|\nE |---------------------------------|\nB |---------5b----------------------|\nF#|--7--7-7----7-5-------------5/7--|\nC#|----------------7-6-5-3-0---3/5--|"
        }
    },
    {
        "song_title": "Supernaut",
        "album": "Vol. 4",
        "trivia": "Frank Zappa and John Bonham both called this their favorite track of all time. It’s got a real bouncy, hyper-rhythmic groove that makes you want to move. I used to do a real flashy shuffle behind the line of scrimmage that had the same kind of swagger. The defense was completely mesmerized, man.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
import json

# Master dataset of 50 Ozzy Osbourne SOLO ERA tracks with Uncle Rico style trivia and tabs
ozzy_solo_dataset = [
    {
        "song_title": "I Don't Know",
        "album": "Blizzard of Ozz",
        "trivia": "The high-octane opening track of Ozzy's solo career, featuring Randy Rhoads using rapid left-hand muting techniques to create a jagged rhythm. People ask me all the time how I didn't make the professional draft, and my answer is always the same: I don't know, man. The system was rigged against a legend.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------7-----|\nD|--7--7p5-7--7/9----7--7p5--7-----|\nA|--5--5p3-5--5/7----5--5p3--5-----|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Crazy Train",
        "album": "Blizzard of Ozz",
        "trivia": "Randy Rhoads wrote this legendary signature riff using a minor scale pattern that sounds like an absolute runaway train locomotive. If I had Randy backing me up during my commercial pitches, we’d have sold out our entire inventory by noon. I'm completely onboard this crazy train, man. Pure classic.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|-------------------5-------------|\nA|--2-2---5-5---4-4--3--5---4------|\nE|--0-0---3-3---2-2-----3---2------|"
        }
    },
    {
        "song_title": "Goodbye to Romance",
        "album": "Blizzard of Ozz",
        "trivia": "Ozzy's formal farewell to Black Sabbath, tracked with a beautiful, emotional melody. Man, saying goodbye to romance is tough, but saying goodbye to my football legacy because of Coach’s bad decisions is the real tragedy. This progression has real soul, much like my late-night driving thoughts.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------0---------------2--------|\nB|------2---2-----------3---3------|\nG|----2-------2-------2-------2----|\nD|--2-----------2---0-----------0--|\nA|---------------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Dee",
        "album": "Blizzard of Ozz",
        "trivia": "A short, beautiful classical guitar instrumental Randy Rhoads wrote for his mother, Delores. I have an immense appreciation for fine acoustic fretwork. Back in '82, I used to strum a few delicate chords by the campfire to get the attention of the head cheerleader. I had smooth mechanics, no lie.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------2-3-2-0---0--------------|\nB|------3---------3---3------------|\nG|----2----------------------------|\nD|--0------------------------------|\nA|---------------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Suicide Solution",
        "album": "Blizzard of Ozz",
        "trivia": "Written about the tragic passing of AC/DC's Bon Scott, featuring a heavy, looping palm-muted drone riff from Randy. The local town council tried to blame my high-speed custom van driving on rock music back in the day, but it’s all about the adrenaline, man. This loop is pure muscle.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|--2-2-4-2-5-2-4-2--2-2-4-2-5-2---|\nE|--0-0-0-0-0-0-0-0--0-0-0-0-0-0---|"
        }
    },
    {
        "song_title": "Mr. Crowley",
        "album": "Blizzard of Ozz",
        "trivia": "Features an absolutely stunning, majestic pipe-organ intro before Randy Rhoads delivers two of the greatest melodic guitar solos in human history. It takes supreme precision to match this track's energy. I used to deliver that exact level of dramatic excellence during our game intro tunnels back in '82.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------7--10--9--7-------------|\nD|--7--10--------------10--9--7----|\nA|---------------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "No Bone Movies",
        "album": "Blizzard of Ozz",
        "trivia": "A fun, upbeat rock tune about the band's addiction to watching low-budget adult films on tour. It's got a driving, classic rock 'n' roll bounce. Man, tour buses and highway miles are a lifestyle I understand completely, living out of my vehicle while tracking new sales territories. Real hustle.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------5-----|\nD|--7--7-7--5--7------5--5-5--5----|\nA|--5--5-5--3--5------3--3-3--3----|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Revelation (Mother Earth)",
        "album": "Blizzard of Ozz",
        "trivia": "An absolute progressive masterpiece that features classical acoustic fingerpicking combined with heavy, apocalyptic stadium rock riffs. Randy Rhoads was a true musical architect. I have a real appreciation for fine engineering, whether it's an epic ballad or custom fiberglass van modifications.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|--------0---------------1--------|\nB|------1---1-----------3---3------|\nG|----2-------2-------2-------2----|\nD|--2-----------2---0-----------0--|\nA|---------------------------------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Steal Away (The Night)",
        "album": "Blizzard of Ozz",
        "trivia": "The lightning-fast, high-tempo closer of their debut solo album. Randy's hands are absolutely flying across the fretboard. I used to steal away into the night back in high school after setting a new regional passing record. The world was mine for the taking, before things went south.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|--9\\8-----8\\7-----7\\6------------|\nA|--7\\6-0-0-6\\5-0-0-5\\4-0-0-5------|\nE|--------------------------3------|"
        }
    },
    {
        "song_title": "Over the Mountain",
        "album": "Diary of a Madman",
        "trivia": "Lee Kerslake starts this off with a legendary, explosive drum roll before Randy hits you with a heavy, driving riff. Over the mountain? Man, that is my absolute mantra! If Coach had put me in during the fourth quarter, I’d have thrown a pigskin clean over those mountains. No doubt. Perfect song.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------4-----------|\nD|--4--4p2-4--4/6---2--2--4--------|\nA|--2--2p0-2--2/4---0-----2--------|\nE|---------------------------------|"
        }
    },
    {
        "song_title": "Flying High Again",
        "album": "Diary of a Madman",
        "trivia": "A real catchy, stadium-ready hard rock anthem with a solo from Randy that features incredible two-handed tapping techniques. It’s about feeling unstoppable. I get that exact same feeling when I look at my old high school highlights tape. I was flying high back then, man. Unbeatable form.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------2-----------|\nA|--4---2-4--2-4---2---0--4--------|\nE|--2-0-0-2-0-2-0-2-0-----2--------|"
        }
    },
    {
        "song_title": "You Can't Kill Rock and Roll",
        "album": "Diary of a Madman",
        "trivia": "A powerful, defiant track attacking the record industry suits who tried to control Ozzy's vision. You can't kill rock and roll, and you certainly can't kill my reputation as the finest option-quarterback this county has ever seen. They try to suppress my records, but the truth remains.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|------3--------------------------|\nG|----2---2---------0--------------|\nD|--0-------------2---2------------|\nA|--------------3------------------|\nE|------------1--------------------|"
        }
    },
    {
        "song_title": "Believer",
        "album": "Diary of a Madman",
        "trivia": "Starts with a very sinister, heavy bass loop before Randy's jagged guitar riff cuts right through the mix like a knife. You gotta be a true believer to survive the sales grind out here on the road, man. If I didn't believe in my own legendary potential, I’d have given up years ago. Crushing tune.",
        "main_riff_tab": {
            "tuning": "Standard (E A D G B E)",
            "notation": "E|---------------------------------|\nB|---------------------------------|\nG|---------------------------------|\nD|---------------------------------|\nA|------5---4---3---2---3p2--------|\nE|--0-0---0---0---0---0-----3-2----|"
        }
    },
    {
        "song_title": "Little Dolls",
        "album": "Diary of a Madman",
