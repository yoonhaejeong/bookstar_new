from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('User must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(verbose_name="email", max_length=100, unique=True)
    user_id = models.CharField(max_length=30, blank=True, null=True)
    profile_image=models.TextField(blank=True, null=True)
    thumbnail = models.CharField(max_length=256, default='default_profile.jpg', blank=True, null=True)

    is_staff = models.BooleanField(default=False)      # 관리자 페이지 접근 여부
    is_active = models.BooleanField(default=True)      # 계정 활성화 여부
    is_superuser = models.BooleanField(default=False)  # 모든 권한 여부

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'users'


class Follow(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # 로그인한 사람
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')    # 팔로우 대상
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"
