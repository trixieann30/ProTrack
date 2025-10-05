from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Mark email as verified when user signs in with Google
        """
        if sociallogin.is_existing:
            return
        
        if 'email' in sociallogin.account.extra_data:
            email = sociallogin.account.extra_data['email']
            email_verified = sociallogin.account.extra_data.get('verified_email', False)
            
            # Mark the user's email as verified
            if email_verified and sociallogin.user:
                sociallogin.user.email_verified = True
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and mark email as verified for Google sign-ins
        """
        user = super().save_user(request, sociallogin, form)
        
        # If signing in with Google, mark email as verified
        if sociallogin.account.provider == 'google':
            user.email_verified = True
            user.save()
        
        return user
