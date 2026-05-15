## ADDED Requirements

### Requirement: Upgrade Flex Message includes skill unlock announcement

The upgrade Flex Message displayed upon title advancement SHALL include a skill unlock section below the upgrade message body.

The skill unlock section SHALL display:
- The skill name (e.g.,「肉盾」「絕對滷域」「魯拉（ルラ）」「滷界敕令」)
- The unlock announcement text defined per title level

Unlock announcement text per title:

**肉汁騎士 (Lv.1)**:
> 技能解鎖：肉盾
>
> 大叔的第一個禮物。
> 輸入「肉盾」，告訴大叔你想去吃哪家，
> 大叔會依照你的口味偏好，幫你先擋雷。

**滷鍋守護者 (Lv.2)**:
> 技能解鎖：絕對滷域
>
> 你打卡過的魯肉飯店，
> 已經開始形成專屬守護領域。
>
> 從現在開始，可以用地圖查看自己的魯肉飯版圖。

**魯肉飯勇者 (Lv.3)**:
> 技能解鎖：魯拉
>
> 吃過的店，
> 都將成為你的傳送據點。
>
> 輸入「魯拉」，
> 選擇曾經攻略過的店，
> 即可一鍵開啟 Google Maps 導航，
> 回到那碗熟悉的魯肉飯。

**魯肉飯大神 (Lv.4)**:
> 技能解鎖：滷界敕令
>
> 你已不只是吃飯的人，
> 而是能向眾勇者發布推薦的大神。
>
> 輸入「號令」，
> 選擇你認可的魯肉飯店，
> 留下推薦理由，
> 讓它登上大神推薦牆。

#### Scenario: User upgrades to 肉汁騎士

- **WHEN** a user's title advances to「肉汁騎士」
- **THEN** the upgrade Flex Message SHALL include the 肉盾 skill unlock announcement

#### Scenario: User upgrades to 滷鍋守護者

- **WHEN** a user's title advances to「滷鍋守護者」
- **THEN** the upgrade Flex Message SHALL include the 絕對滷域 skill unlock announcement

#### Scenario: User upgrades to 魯肉飯勇者

- **WHEN** a user's title advances to「魯肉飯勇者」
- **THEN** the upgrade Flex Message SHALL include the 魯拉 skill unlock announcement

#### Scenario: User upgrades to 魯肉飯大神

- **WHEN** a user's title advances to「魯肉飯大神」
- **THEN** the upgrade Flex Message SHALL include the 滷界敕令 skill unlock announcement
