import feedparser

RSS_URL = "https://www.freelancermap.com/feeds/projects/int-international.xml"

class Freelancermap:

    @staticmethod
    def parse_feeds() -> list[dict]:
        jobs = []
        
        feed = feedparser.parse(RSS_URL)

        for entry in feed.entries:
            title = entry.title
            description = entry.summary
            link = entry.link
            published = entry.published
            company = entry.company

            jobs.append({
                "title": title,
                "company": company,
                "description": description,
                "link": link,
                "published": published
            })
    
        return jobs