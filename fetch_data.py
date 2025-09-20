def load_seen_urls_from_csv(self):
    with open(self.csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None) 
        for row in reader:
            href = row[0].strip()
            self.hrefs.append(href)
    return self.hrefs


def fetch_picks_data(self):
    read = self.load_seen_urls_from_csv()
    for i, href in enumerate(read):
        self.driver.get(href)
        print(f"\nSuccessfully navigated to Pick url :{href}, Pick number :{i+1}/{len(read)+1} ")
        self.scroll_page()

        #Find the NFL Picks
        names = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "col-12")))
        value = names.find_element(By.XPATH, ".//p").text.strip()
        players_part = value.split("for")[1].split("game")[0].strip()
        player1, player2 = [t.strip() for t in players_part.split("/")]
        print(f"The Picks Palyers was :{players_part}")

        #Find the winner and the loser
        winner = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "pad"))).text.strip()   
        print(f"The winner name is :{winner[8:]}")
        winner_name = winner[8:]

        if winner_name == player1:
            loser_name = player2
        elif winner_name == player2:
            loser_name = player1
        print(f"The loser name is :{loser_name}")

        #Find game info
        game_information = WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-4.col-xs-12 p")))
        text_content = game_information.get_attribute("innerText")
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]

        for line in lines:
            if line.startswith("Game Day:"):
                scraped_day = line.split(":", 1)[1].strip()
                self.match_day = datetime.strptime(scraped_day, "%A, %b %d, %Y")
            elif line.startswith("Station:"):
                self.station = line.split(":", 1)[1].strip()
            elif line.startswith("Projected Score:"):
                self.scores = line.split(":", 1)[1].strip()
                scores_str = self.scores.strip().split()
                if scores_str[0] > scores_str[1]:
                    self.winner_score, self.loser_score = scores_str[0], scores_str[1]
                else:
                    self.winner_score, self.loser_score = scores_str[1], scores_str[0]
                        
        print("Match Day:",self.match_day)
        print("Station:",self.station)
        print("Winner Score:",self.winner_score)
        print("Loser Score:",self.loser_score)

        #Find organization and expert
        tables = WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "responsiveSmaller")))
        for table in tables:
            organization = table.find_element(By.XPATH, ".//tbody/tr[1]/td[1]").text.strip()
            expert = table.find_element(By.XPATH, ".//tbody/tr[1]/td[2]").text.strip()
            print(f"Organization :{organization}")
            print(f"Expert :{expert}")

    
        self.save_to_db(winner_name, loser_name, self.winner_score, self.loser_score, self.station, self.match_day, expert, organization)

            
def save_to_db(self, winner_name, loser_name,winner_score,loser_score,station,match_day,expert,organization):
    names_list = (winner_name,loser_name,winner_score,loser_score,station,match_day,expert,organization)
    self.cursor.execute(f"INSERT INTO nerd (winner, loser, wscor, lscor, station, gameday, expert, organized) VALUE (%s, %s,%s, %s,%s, %s,%s, %s)", names_list)
    self.connection.commit()
    print(f"{names_list} was added successfully to database")
