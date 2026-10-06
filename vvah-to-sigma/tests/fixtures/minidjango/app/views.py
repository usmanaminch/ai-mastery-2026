def csrf_exempt(f):
    return f


def register(request):
    return None


@csrf_exempt
def sql_lab(request):
    q = "select * from users where name='%s'" % request.GET["name"]
    return q


def cart(request):
    return None


class Item:
    def get(self, request, pk):
        return pk


def post_lab(request):
    return request.POST.get("cmd")
