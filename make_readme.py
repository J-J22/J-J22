"""Writes README.md: two lines of text, everything else is the animated pixel assets (dark/light via <picture>)."""
RAW = "https://raw.githubusercontent.com/J-J22/J-J22/main/"
GRID = 412   # make_assets.py grid: every width below is a share of it, so all edges line up at any page width


def pct(px):
    return f"{px / GRID * 100:.2f}%"


def pic(path, alt, width=None):
    w = f' width="{width}"' if width else ""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}{path}-dark.gif">'
            f'<img alt="{alt}" src="{RAW}{path}-light.gif"{w}></picture>')


def link(url, inner):
    return f'<a href="{url}">{inner}</a>'


def h(label):
    return pic(f"assets/h-{label.replace(' ', '-')}", label, "100%")


cards = [("reiatsuflow", "https://github.com/J-J22/reiatsuflow", "ReiatsuFlow, study planner for linux"),
         ("smriti", "https://github.com/J-J22/smriti", "Smriti, offline app for dementia care"),
         ("vision", "https://github.com/J-J22/Vision", "Vision, ai agents from idea to deployment"),
         ("portfolio", "https://j-j22.github.io", "Portfolio, my pixel site")]
grid = "".join(link(u, pic(f"assets/card-{k}", alt, "50%")) for k, u, alt in cards)
buttons = "".join(link(u, pic(f"assets/btn-{k}", alt, w)) for k, u, alt, w in (
    ("linkedin", "https://www.linkedin.com/in/joc22/", "linkedin", pct(8 * 8 + 30)),
    ("portfolio", "https://j-j22.github.io", "portfolio", pct(8 * 9 + 30)),
    ("email", "mailto:jaiwardhanjoshi@gmail.com", "jaiwardhanjoshi@gmail.com", pct(8 * 5 + 30))))
snake = ('<picture><source media="(prefers-color-scheme: dark)" '
         f'srcset="https://raw.githubusercontent.com/J-J22/J-J22/output/github-snake-dark.svg">'
         '<img alt="snake eating my contribution graph" '
         'src="https://raw.githubusercontent.com/J-J22/J-J22/output/github-snake.svg" width="100%"></picture>')

README = f"""{pic("banner", "JoC, jaiwardhan joshi, cse @ jecrc, jaipur", "100%")}

Hey, I'm Jai, I go by JoC here. Second year CSE at JECRC in Jaipur, Learning Cloud Computing, Making Projects hackathons all at once so yeah... busy

{h("projects")}

{grid}

{h("quest log")}

{pic("assets/quests", "AWS SAA feb 2027, Leetcode 500, hackathon build dec 2026, http server on the side", "100%")}

{h("inventory")}

{pic("assets/inventory", "python, c++, c, java, bash, git, aws, linux. targets Leetcode 500, AWS SAA. arch + hyprland, bleach rice", "100%")}

{h("contributions")}

{snake}

{h("find me")}

{buttons}
"""
open("README.md", "w").write(README.replace(f'{RAW}banner', f'{RAW}banner'))
print("ok")
