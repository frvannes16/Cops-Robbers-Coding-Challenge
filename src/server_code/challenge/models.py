from django.urls import reverse
from django.db import models
from django.core.cache import cache

import random
import string

class Game(models.Model):
    cop_team = models.ForeignKey('Team', related_name='cops')
    robber_team = models.ForeignKey('Team', related_name='robbers')
    has_ended = models.BooleanField(default=False)
    cop_score = models.IntegerField(default=0)
    robber_score = models.IntegerField(default=0)
    winner = models.ForeignKey('Team', null=True, blank=True)


    @classmethod
    def create(cls, cops, robbers):
        # If a new game is being created, we should invalidate the old game cache.
        game = cls(cop_team=cops, robber_team=robbers)
        game.save()
        return game

    @classmethod
    def get_game(cls, a_code, b_code, active_matters=True):
        a = Team.objects.get(code=a_code)
        b = Team.objects.get(code=b_code)
        if a.team_type == "ROBBERS" and b.team_type == "COPS":
            if active_matters:
                game = Game.objects.filter(cop_team=b, robber_team=a, has_ended=False)
                game = game.first() if game.exists() else None
            else:
                game = Game.objects.filter(cop_team=b, robber_team=a).first()
        elif a.team_type == b.team_type:
            game = None
        else:
            game = Game.objects.filter(cop_team=a, robber_team=b, has_ended=False)
            game = game.first() if game.exists() else None
        return game


    def end_game(self):
        self.has_ended = True
        self.save()
        cache.set(self.get_game_key(), {'STATUS': 'GAME_OVER'})
        cache.set(self.get_maze_key(), None)


    def get_game_key(self):
        return "-".join(sorted([self.cop_team.code, self.robber_team.code]))

    def get_maze_key(self):
        return self.get_game_key() + '_maze'

    def get_group_key(self):
        return self.get_game_key()

    def get_game_lock(self):
        return self.get_game_key() + '_lock'

    def remove_from_cache(self):
        '''
        Invalidates the game in the cache. Deletes the maze, player positions, and any metadata.
        '''
        cache.set(self.get_game_key(), None)
        cache.set(self.get_maze_key(), None)


    def get_absolute_url(self):
        return reverse('challenge:watch-game', args=[self.cop_team.code, self.robber_team.code])

    def __str__(self):
        return "Game: " + self.cop_team.name + " vs. " + self.robber_team.name

    def __repr__(self):
        return str(self)


class Member(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey('Team')

    def __str__(self):
        return self.team.name + ": " + self.name

    def __repr__(self):
        return str(self)


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    team_type = models.CharField(max_length=20)
    code = models.CharField(max_length=5, unique=True)

    @classmethod
    def create(cls, name):
        # check if team name already exists.
        if cls.objects.filter(name=name).exists():
            return False
        # Generate team code.
        code = ''.join([random.choice(string.ascii_lowercase) for i in range(5)])
        while cls.objects.filter(code=code).exists():
            code = ''.join(random.choices(string.ascii_lowercase, k=5))
        # Check redis cache for switching team type.
        team_type = cache.get_or_set('team_type', 'COPS', None)
        if team_type == 'COPS':
            cache.set('team_type', 'ROBBERS', None)
        else:
            cache.set('team_type', 'COPS', None)
        team = cls(name=name, code=code, team_type=team_type)
        team.save()
        return team

    def __repr__(self):
        return "Team: " + self.name + "/" + self.code

    def __str__(self):
        return "Team: " + self.name


class Settings(models.Model):
    name = models.CharField(max_length=100, unique=True)
    num_cops = models.IntegerField()
    num_robbers = models.IntegerField()
    num_banks = models.IntegerField()
    rows = models.IntegerField()
    cols = models.IntegerField()
    labyrinth_degree = models.DecimalField(decimal_places=5, max_digits=6)

    robbers_code_link = models.CharField(max_length=300, help_text="Link to Robbers student code", blank=True)
    cops_code_link = models.CharField(max_length=300, help_text="Link to Cops student code", blank=True)


    @classmethod
    def get_default(cls):
        if cls.objects.filter(name='default').exists():
            return cls.objects.get(name='default')
        else:
            # Create default settings
            settings = cls(name='default', num_cops=2, num_robbers=2, num_banks=3, rows=30, cols=30, labyrinth_degree=0.3)
            settings.save()
            return settings
