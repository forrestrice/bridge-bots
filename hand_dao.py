import psycopg2
import json
#
from deal.deal import Deal


class HandDao:
    def __init__(self):
        self.connection = psycopg2.connect("dbname=bridge user=bridgebot host=localhost password=bidslam")

    def close(self):
        self.connection.close()

    def get_processed_files(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT file_name FROM recap_files")
            processed_files_tuples = cursor.fetchall()
            return [x[0] for x in processed_files_tuples]

    def record_porcessed_file(self, file_name):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO recap_files VALUES (%s)", (file_name,))
        self.connection.commit()



    def write_hand(self, hand):
        print("Writing hand")
        with self.connection.cursor() as cursor:
            north = hand.north_hand
            east = hand.east_hand
            south = hand.south_hand
            west = hand.west_hand
            try:
                cursor.execute("INSERT INTO hands (dealer, ew_vulnerable, ns_vulnerable, "
                            "nspades, nhearts, ndiamonds, nclubs, "
                            "espades, ehearts, ediamonds, eclubs, "
                            "sspades, shearts, sdiamonds, sclubs, "
                            "wspades, whearts, wdiamonds, wclubs) "
                            "VALUES (%s, %s, %s, "
                            "%s, %s, %s, %s, "
                            "%s, %s, %s, %s, "
                            "%s, %s, %s, %s, "
                            "%s, %s, %s, %s);",
                           (hand.dealer, hand.ew_vulnerable, hand.ns_vulnerable,
                            north.spades, north.hearts, north.diamonds, north.clubs,
                            east.spades, east.hearts, east.diamonds, east.clubs,
                            south.spades, south.hearts, south.diamonds, south.clubs,
                            west.spades, west.hearts, west.diamonds, west.clubs))
                self.connection.commit()
            except Exception as e:
                print(e)

    def write_double_dummy(self, deal: Deal, analysis: json):
        pass



hand_dao = HandDao()
hand_dao.record_porcessed_file("test_file.txt")
print(hand_dao.get_processed_files())