import feedparser

RSS_LIST = ["https://remotive.com/remote-jobs/feed/software-dev", 'https://remotive.com/remote-jobs/feed/data', 
           'https://remotive.com/remote-jobs/feed/devops', 'https://remotive.com/remote-jobs/feed/all-others']

class Remotive:
        
    @staticmethod
    def parse_feeds() -> list[dict]:
        jobs = []
        for rss_url in RSS_LIST:
            feed = feedparser.parse(rss_url)
            try:
                for entry in feed.entries:
                    location = entry.location
                    title = entry.title
                    description = entry.summary
                    category = entry.tags[0].term
                    link = entry.link
                    published = entry.published
                    company = entry.company
                    job_type = entry.type
                    
                    if (job_type != 'full_time'):
                        jobs.append({
                            "title": title,
                            "company": company,
                            "job_type": job_type,
                            "description": description,
                            "category": category,
                            "link": link,
                            "published": published
                        })
            except:
                print(f"Error parsing feed: {rss_url}")
                continue

        return jobs