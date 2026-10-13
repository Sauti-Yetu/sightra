def supabase_auth(request):
    return {
        "supabase_user": getattr(request, "supabase_user", None),
    }
