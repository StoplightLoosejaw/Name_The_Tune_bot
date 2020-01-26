import random
import re
import os
import psycopg2


class TuneEngine:
    def __init__(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.conn.cursor()

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS CURRENT_GAME ( USER_ID text," \
                                                        " DECADE int," \
                                                        " GENRE text," \
                                                        " LYRICS text," \
                                                        " CORRECT_ARTIST text, CORRECT_TRACK text," \
                                                        " INCORRECT_ARTISTS text)"
        stmt_users = "CREATE TABLE IF NOT EXISTS ALL_USERS ( USER_ID text, USER_NAME text, GAME_PHASE int," \
                     " WINS integer, LOSSES integer, IMAGES_FLG integer,  LEADERBOARD_FLG integer, LANG_FLG integer )"

        self.cursor.execute(stmt)
        self.cursor.execute(stmt_users)
        self.conn.commit()

    def drop(self):
        stmt = "DROP TABLE CURRENT_GAME"
        stmt_users = "DROP TABLE ALL_USERS"
        self.cursor.execute(stmt)
        self.cursor.execute(stmt_users)
        self.conn.commit()

    def add_row_current_game(self, arcg_user_id, arcg_decade,
                             arcg_genre, arcg_lyrics, arcg_correct_artist, arcg_correct_track, arcg_incorrect_artists):
        stmt = "INSERT INTO CURRENT_GAME (USER_ID, DECADE," \
               "GENRE, LYRICS, CORRECT_ARTIST,  CORRECT_TRACK, INCORRECT_ARTISTS) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        args = (str(arcg_user_id), str(arcg_decade),
                arcg_genre, arcg_lyrics, arcg_correct_artist, arcg_correct_track, arcg_incorrect_artists, )
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def add_row_all_users(self, arau_user_id, arau_user_name, arau_game_phase,
                          arau_wins, arau_losses, arau_images_flg, arau_leaderboard_flg, arau_lang_flg):
        stmt = "INSERT INTO ALL_USERS (USER_ID, USER_NAME, GAME_PHASE, WINS," \
               "LOSSES, IMAGES_FLG, LEADERBOARD_FLG, LANG_FLG) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        args = (str(arau_user_id), arau_user_name, arau_game_phase,
                str(arau_wins), str(arau_losses), str(arau_images_flg), str(arau_leaderboard_flg),
                str(arau_lang_flg))
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def delete_row(self, dr_table_name, dr_user_id):
        stmt = "DELETE FROM {} WHERE USER_ID =  %s".format(dr_table_name)
        args = (str(dr_user_id), )
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def update_field(self, uf_table_name, uf_field_name, uf_field_value, uf_user_id):
        if uf_field_name in ('DECADE', 'WINS', 'LEADERBOARD_FLG', 'LOSSES', 'IMAGES_FLG', 'LANG_FLG', 'MISTAKES'):
            stmt = "UPDATE {} SET {} = {} WHERE USER_ID = '{}'".format(uf_table_name, uf_field_name,
                                                                       uf_field_value, uf_user_id)
        else:
            stmt = "UPDATE {} SET {} = '{}' WHERE USER_ID = '{}'".format(uf_table_name, uf_field_name,
                                                                         uf_field_value, uf_user_id)
        self.cursor.execute(stmt)
        self.conn.commit()

    def get_items(self, gi_table_name, gi_field_name, gi_user_id):
        stmt = "SELECT {} FROM {} WHERE USER_ID = '{}'".format(gi_field_name, gi_table_name, gi_user_id)
        self.cursor.execute(stmt)
        try:
            return self.cursor.fetchone()[0]
        except:
            return False

    def get_all_genre(self):
        stmt = 'SELECT DISTINCT GENRE FROM "LYRICS" '
        self.cursor.execute(stmt)
        try:
            return self.cursor.fetchall()
        except:
            return False

    def new_player(self, np_user_id):
        self.add_row_all_users(np_user_id, 0, 0, 0, 0, 1, 3, 1)
        self.add_row_current_game(np_user_id, 0, 0, 0, 0, 0, 0)

    def new_game(self, ng_user_id, ng_decade, ng_genre, ng_lyrics, ng_correct_artist,  ng_correct_track,
                 ng_incorrect_artists):
        self.delete_row('CURRENT_GAME', ng_user_id)
        self.add_row_current_game(ng_user_id, ng_decade, ng_genre, ng_lyrics, ng_correct_artist, ng_correct_track,
                                  ng_incorrect_artists)

    def player_wins(self, pw_user_id):
        pw_artist = self.get_items('CURRENT_GAME', 'CORRECT_ARTIST', pw_user_id)
        new_wins = self.get_items('ALL_USERS', 'WINS', pw_user_id)+1
        self.update_field('ALL_USERS', 'WINS', new_wins, pw_user_id)
        return pw_artist

    def player_loses(self, pw_user_id):
        pw_artist = self.get_items('CURRENT_GAME', 'CORRECT_ARTIST', pw_user_id)
        new_losses = self.get_items('ALL_USERS', 'LOSSES', pw_user_id)+1
        self.update_field('ALL_USERS', 'LOSSES', new_losses, pw_user_id)
        return pw_artist

    def get_track(self, gt_user_id, gt_genre):
        stmt = '''SELECT ARTIST, LYRICS, T.TRACK FROM "LYRICS" L JOIN "TRACKS" T ON L.TRACK=T.TRACK
                WHERE LOWER(GENRE) = LOWER('{}') ''' \
               '''ORDER BY RANDOM() LIMIT 1'''.format(gt_genre)
        gt_short_lyrics = []
        while len(gt_short_lyrics)<20:
            self.cursor.execute(stmt)
            select_res = self.cursor.fetchall()[0]
            gt_correct_artist = select_res[0]
            gt_lyrics = select_res[1].split('\n\n')
            gt_track = select_res[2]
            gt_rand = random.randint(0, len(gt_lyrics)-1)
            gt_short_lyrics = gt_lyrics[gt_rand]
            if gt_correct_artist in gt_short_lyrics:
                gt_short_lyrics=[]
        stmt = '''SELECT ARTIST FROM (SELECT DISTINCT ARTIST FROM "LYRICS" L JOIN "TRACKS" T '''\
               '''ON L.TRACK=T.TRACK WHERE LOWER(GENRE) = '{}' ''' \
               '''AND ARTIST <> '{}') A ORDER BY RANDOM() LIMIT 3'''.format(gt_genre, gt_correct_artist.replace("'", ''))
        self.cursor.execute(stmt)
        gt_incorrect_artists = self.cursor.fetchall()
        gt_incorrect_artists = gt_incorrect_artists[0][0] + ',' + gt_incorrect_artists[1][0] + ',' + \
                               gt_incorrect_artists[2][0]
        self.new_game(gt_user_id, 1000, gt_genre, gt_short_lyrics, gt_correct_artist, gt_track, gt_incorrect_artists)
        return gt_short_lyrics

    def get_leaderboard(self):
        stmt = '''SELECT ROW_NUMBER() OVER (ORDER BY WINS DESC, LOSSES ASC) AS I, '''\
               '''USER_NAME, 'УГАДАНО '||WINS, 'ОШИБОК '||LOSSES FROM ALL_USERS  ''' \
               ''' WHERE LEADERBOARD_FLG=1 ORDER BY WINS DESC, LOSSES ASC LIMIT 10'''
        self.cursor.execute(stmt)
        leaderboard = self.cursor.fetchall()
        return "\n".join(" ".join(map(str, x)) for x in leaderboard)

    def get_players_position(self, gpp_user_id):
        stmt = '''SELECT I, USER_NAME, WINS, LOSSES FROM ( '''\
         '''SELECT ROW_NUMBER() OVER (ORDER BY WINS DESC, LOSSES ASC) AS I, '''\
         '''USER_NAME, USER_ID, WINS, LOSSES FROM ALL_USERS  ''' \
         '''WHERE LEADERBOARD_FLG=1 ORDER BY WINS DESC, LOSSES ASC) A  ''' \
         '''WHERE USER_ID='{}' '''.format(gpp_user_id)
        self.cursor.execute(stmt)
        players_pos = self.cursor.fetchone()
        return players_pos[0]

    def game_begin(self, gb_user_id):
        gb_genre = self.get_items('CURRENT_GAME', 'GENRE', gb_user_id)
        if not self.get_items('ALL_USERS', 'USER_ID', gb_user_id):
            self.new_player(gb_user_id)
        self.get_track(gb_user_id, gb_genre)
