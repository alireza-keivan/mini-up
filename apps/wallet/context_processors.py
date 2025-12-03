# apps/wallet/context_processors.py

def wallet_context(request):
    """
    اضافه کردن اطلاعات کیف پول به تمام templates
    """
    context = {
        'wallet_balance': 0,
        'wallet_gift_balance': 0,
        'wallet_total_balance': 0,
    }
    
    if request.user.is_authenticated:
        try:
            from apps.wallet.models import Wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            context['wallet_balance'] = wallet.balance
            context['wallet_gift_balance'] = wallet.gift_balance
            context['wallet_total_balance'] = wallet.total_balance
            context['user_wallet'] = wallet
        except Exception:
            pass
    
    return context
