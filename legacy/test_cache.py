from database import news_collection
from datetime import datetime, timedelta

# Check what's in MongoDB
docs = list(news_collection.find())
print(f'Total docs in DB: {len(docs)}')

for d in docs:
    print(f'Query: {d["query"]}')
    print(f'Time: {d["timestamp"]}')
    print('---')

# Check cache specifically
cutoff = datetime.utcnow() - timedelta(hours=1)
print(f'\nCutoff time: {cutoff}')
print(f'Current time: {datetime.utcnow()}')

cached = news_collection.find_one({
    "query": "Iran war 2026",
    "timestamp": {"$gte": cutoff}
})
print(f'\nCache result: {cached}')