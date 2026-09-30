import pygame
import random
import json
from game.player import Player,LANE_W
from game.traffic import Car,make_car,make_raft

LANES=8
WIDTH=LANES*LANE_W
HEIGHT=600
FPS=60
BG=(60,60,60)
HIGH_SCORE_FILE="high_scores.json"

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Traffic Escape")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("monospace",24,bold=True)
        self.big_font=pygame.font.SysFont("monospace",44,bold=True)
        self.high_scores=self.load_high_scores()
        self.reset()

    def reset(self):
        self.player=Player(WIDTH//2,HEIGHT-80)
        self.cars=[]
        self.raft_lane=3
        self.raft=make_raft(self.raft_lane,HEIGHT//2-40)
        self.timer=0
        self.spawn_interval=50
        self.speed=3
        self.score=0
        self.lives=3
        self.score_recorded=False
        self.day_night_start=pygame.time.get_ticks()
        self.night_mode=False
        self.game_over=False
        self.won=False

    def load_high_scores(self):
        """Load the persistent top-5 scores.

        Missing, invalid, or corrupted JSON is treated as an empty
        high-score table so the game can still start normally.
        """
        try:
            with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
                data=json.load(f)

            if not isinstance(data, list):
                return []

            scores=[]
            for value in data:
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    scores.append(int(value))

            return sorted(scores, reverse=True)[:5]
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
            return []

    def save_high_scores(self):
        """Save the current top-5 scores without crashing the game."""
        try:
            with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.high_scores[:5], f, indent=2)
        except (OSError, TypeError, ValueError):
            # A file-system problem should not stop gameplay.
            pass

    def record_score(self):
        """Add the finished game's score to the persistent top five."""
        if self.score_recorded:
            return

        final_score=self.score//10
        self.high_scores.append(final_score)
        self.high_scores=sorted(self.high_scores, reverse=True)[:5]
        self.save_high_scores()
        self.score_recorded=True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r: self.reset()
        return True

    def update_day_night(self):
        # Use elapsed real time rather than frame count, so the cycle does
        # not freeze or speed up when the frame rate changes.
        elapsed=pygame.time.get_ticks()-self.day_night_start
        self.night_mode=(elapsed//30000)%2==1

    def update(self):
        self.update_day_night()

        if self.game_over or self.won: return

        keys=pygame.key.get_pressed()
        # The dedicated raft lane can only be entered while the player
        # overlaps the moving raft.
        requested_dx=0
        requested_dy=0
        if self.player.move_cooldown<=0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: requested_dx=-LANE_W
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: requested_dx=LANE_W
            if keys[pygame.K_UP] or keys[pygame.K_w]: requested_dy=-8
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: requested_dy=8

        proposed=self.player.rect.copy()
        if requested_dx:
            proposed.x=max(0,min(WIDTH-proposed.width,proposed.x+requested_dx))
        if requested_dy:
            proposed.y=max(0,proposed.y+requested_dy)

        proposed_lane=proposed.centerx//LANE_W
        current_lane=self.player.rect.centerx//LANE_W

        entering_raft_lane = proposed_lane==self.raft_lane and current_lane!=self.raft_lane
        already_in_raft_lane = current_lane==self.raft_lane

        on_raft=self.player.rect.colliderect(self.raft.rect)

        if entering_raft_lane and not proposed.colliderect(self.raft.rect):
            requested_dx=0
            requested_dy=0
        elif already_in_raft_lane and not on_raft:
            requested_dx=0
            requested_dy=0

        if requested_dx or requested_dy:
            class _Keys:
                def __getitem__(self,key):
                    if key in (pygame.K_LEFT, pygame.K_a):
                        return requested_dx < 0
                    if key in (pygame.K_RIGHT, pygame.K_d):
                        return requested_dx > 0
                    if key in (pygame.K_UP, pygame.K_w):
                        return requested_dy < 0
                    if key in (pygame.K_DOWN, pygame.K_s):
                        return requested_dy > 0
                    return False

            self.player.move(_Keys(),0,WIDTH)

        # Move the raft. If the player is standing on it, carry the player
        # by exactly the same horizontal displacement.
        if self.player.rect.colliderect(self.raft.rect):
            dx=self.raft.update(0,WIDTH)
            self.player.rect.x+=dx
            self.player.rect.x=max(0,min(WIDTH-self.player.rect.width,self.player.rect.x))
        else:
            self.raft.update(0,WIDTH)

        self.timer+=1
        if self.timer>=self.spawn_interval:
            lane=random.randint(0,LANES-1)

            # The raft lane remains free of normal traffic.
            while lane==self.raft_lane:
                lane=random.randint(0,LANES-1)

            self.cars.append(make_car(lane,HEIGHT,self.speed))
            self.timer=0
            self.spawn_interval=max(22,self.spawn_interval-0.2)

        for c in self.cars:
            c.update()
            if c.rect.colliderect(self.player.rect):
                self.lives-=1
                self.player=Player(WIDTH//2,HEIGHT-80)
                self.cars.remove(c)

                if self.lives<=0:
                    self.lives=0
                    self.game_over=True
                    self.record_score()
                break

        self.cars=[c for c in self.cars if not c.off_screen(HEIGHT)]

        self.score+=1
        if self.score%300==0: self.speed=min(10,self.speed+0.5)
        if self.player.rect.top<=10:
            self.won=True
            self.record_score()

    def draw(self):
        self.screen.fill(BG)
        # road markings
        for i in range(LANES+1):
            pygame.draw.line(self.screen,(100,100,100),(i*LANE_W,0),(i*LANE_W,HEIGHT),2)
        for y in range(0,HEIGHT,60):
            for i in range(LANES):
                pygame.draw.rect(self.screen,(200,200,100),pygame.Rect(i*LANE_W+LANE_W//2-3,y,6,30))
        # Dedicated moving-raft crossing lane.
        pygame.draw.rect(
            self.screen,(45,85,115),
            pygame.Rect(self.raft_lane*LANE_W,30,LANE_W,HEIGHT-80)
        )

        # sidewalks
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,HEIGHT-50,WIDTH,50))
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,0,WIDTH,30))
        for c in self.cars: c.draw(self.screen,self.night_mode)
        self.raft.draw(self.screen)
        self.player.draw(self.screen)

        if self.night_mode:
            # Darken the whole scene while leaving the HUD readable.
            night_overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            night_overlay.fill((8,12,35,145))
            self.screen.blit(night_overlay,(0,0))
        hud=pygame.Rect(0,0,WIDTH,30)
        pygame.draw.rect(self.screen,(20,20,20),hud)
        mode="NIGHT" if self.night_mode else "DAY"
        s=self.font.render(f"Score: {self.score//10}  Lives: {self.lives}  {mode}  GOAL: reach the top!  R=Restart",True,(220,220,220))
        self.screen.blit(s,(6,4))

        if self.game_over:
            self._msg("GAME OVER",(220,60,60))
        if self.won:
            self._msg("YOU MADE IT!",(80,220,80))

        if self.game_over or self.won:
            self._draw_high_scores()

        pygame.display.flip()

    def _draw_high_scores(self):
        """Display the persistent top-5 score table on the end screen."""
        title=self.font.render("TOP 5 SCORES",True,(255,220,100))
        self.screen.blit(
            title,
            (WIDTH//2-title.get_width()//2,HEIGHT//2+70)
        )

        for i, score in enumerate(self.high_scores[:5], start=1):
            row=self.font.render(f"{i}. {score}",True,(230,230,230))
            self.screen.blit(
                row,
                (WIDTH//2-row.get_width()//2,HEIGHT//2+105+(i-1)*28)
            )

    def _msg(self,text,color):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        self.screen.blit(ov,(0,0))
        m=self.big_font.render(text,True,color)
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//2-40))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+20))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
