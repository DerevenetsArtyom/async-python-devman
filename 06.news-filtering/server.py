from aiohttp import web


async def handle(request):
    urls = request.rel_url.query['urls']
    data = {"urls": urls}
    return web.json_response(data)


app = web.Application()

app.add_routes([
    web.get('/', handle),
])

web.run_app(app)
