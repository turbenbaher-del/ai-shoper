# AI-шопер · Дизайн-система Spec

Технический документ для дизайнера или разработчика. Описывает все 10 компонентов с точными размерами, цветами, поведением.

**Платформа:** Telegram Mini App + PWA · Mobile-first · Dark mode by default

---

## 1. Палитра

### Основные
| Назначение | Hex | CSS-переменная |
|------------|-----|----------------|
| Фон основной | `#0A0E13` | `--bg` |
| Поверхности (карточки) | `#161B22` | `--bg-surface` |
| Hover / divider | `#21262D` | `--bg-raised` |
| Hover (повышенный) | `#2D333B` | `--bg-high` |
| Бордеры | `#30363D` | `--border` |

### Текст
| Назначение | Hex | CSS-переменная |
|------------|-----|----------------|
| Текст основной | `#E6EDF3` | `--text` |
| Текст вторичный | `#9198A1` | `--text-mute` |
| Текст-хинт | `#6E7681` | `--text-dim` |

### Акцент (бренд-цвет)
| Назначение | Hex | CSS-переменная |
|------------|-----|----------------|
| **Главный акцент** | **`#00D9A6`** | `--accent` |
| Акцент при hover | `#1FE5B6` | `--accent-bright` |
| Акцент при active | `#00B888` | `--accent-dim` |
| Акцент-подложка 12% | `rgba(0, 217, 166, 0.12)` | `--accent-soft` |

### Семантические
| Назначение | Hex | CSS-переменная |
|------------|-----|----------------|
| Success (выгода, проверено) | `#3FB950` | `--green` |
| Warning (внимание, подорожал) | `#D29922` | `--amber` |
| Danger (накрутка, ошибка) | `#F85149` | `--red` |
| Info (нейтральная инфа) | `#58A6FF` | `--blue` |

### Контрастность (WCAG)
- Текст основной на фоне: 14.7:1 (AAA)
- Акцент на фоне: 6.8:1 (AAA для интерактивных)
- Текст вторичный на фоне: 7.1:1 (AAA)

---

## 2. Типографика

**Шрифт:** Inter (Google Fonts). Подключение:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Веса в использовании:** 400, 500, 600, 700.

### Шкала размеров

| Стиль | Size / LineHeight / Weight | Letter-spacing | Применение |
|-------|---------------------------|----------------|------------|
| Display | 32 / 1.1 / 700 | -0.02em | Большие цифры (цена, экономия) |
| H1 | 24 / 1.25 / 700 | -0.01em | Заголовки экранов |
| H2 | 18 / 1.35 / 600 | 0 | Заголовки секций |
| Body L | 16 / 1.5 / 500 | 0 | Главный текст карточек |
| Body | 14 / 1.5 / 400 | 0 | Обычный текст |
| Caption | 12 / 1.4 / 400 | 0 | Подписи, метки |
| Tiny | 11 / — / 500 | 0.08em UPPERCASE | Бейджи |

### Правила
- Для всех цифр (цены, статистика): `font-variant-numeric: tabular-nums` — одинаковая ширина цифр.
- Никогда не использовать размер меньше 11px.
- Не более 3 размеров на одном экране.
- Не центрировать тексты длиннее 2 строк.

---

## 3. Кнопки

### Базовые параметры
- **Высота по умолчанию:** 44px (Apple HIG minimum for tap-targets)
- **Высота большая:** 52px (для главных CTA)
- **Высота маленькая:** 36px
- **Радиус:** 8px (`--r-md`)
- **Шрифт:** Inter 15px / weight 500
- **Иконка:** 18px, отступ от текста 8px
- **Padding горизонтальный:** 20px (44px), 28px (52px), 14px (36px)

### Типы

**Primary** — главное действие
- Background: `--accent` (#00D9A6)
- Text: `--bg` (#0A0E13)
- Hover: background `--accent-bright`, transform `translateY(-1px)`
- Active: transform `translateY(0)`, background `--accent-dim`

**Secondary** — второстепенное действие
- Background: `--bg-raised` (#21262D)
- Text: `--text`
- Border: 1px `--border`
- Hover: background `--bg-high`, border `--text-dim`

**Ghost** — фоновое действие
- Background: transparent
- Text: `--text`
- Hover: background `--bg-raised`

**Danger** — удаление, отмена
- Background: `rgba(248, 81, 73, 0.1)`
- Text: `--red`
- Border: 1px `rgba(248, 81, 73, 0.2)`

### Состояние disabled
- `opacity: 0.4`
- `cursor: not-allowed`
- Transform не применяется

### Anim
- Transition: `all 200ms cubic-bezier(0.16, 1, 0.3, 1)`

---

## 4. Карточка товара

### Структура (сверху вниз)
1. Header: ранг (🥇/🥈/🥉 + текст) + бейдж "Проверен"
2. Изображение товара (аспект 4:3)
3. Название (Body L 16px / 600)
4. Причина выбора (Caption 12px / 400, `--text-mute`)
5. Блок цен (3 строки: магазин + цена)
6. Кнопки действий: Купить + 2 иконки

### Размеры
- Padding: 16px
- Радиус: 12px (`--r-lg`)
- Между элементами: 12px
- Изображение: background `--bg-raised`, радиус 8px, aspect-ratio 4:3

### Состояние "Победитель"
- Border: 1px `--accent`
- Background: linear-gradient(180deg, rgba(0, 217, 166, 0.04) 0%, `--bg-surface` 100%)
- Медаль 🥇 + бейдж "Проверен"

### Блок цен
- Background: `--bg` (внутри `--bg-surface` создаёт глубину)
- Padding: 10px
- Радиус: 8px
- Цена-победитель: цвет `--accent`, weight 600, size 14
- Остальные цены: monospace `--text`, weight 500, size 12

### Кнопки
- Главная "Купить": Primary small, flex:1 (растягивается)
- Доп. иконки: Secondary small icon-only (36×36)

---

## 5. Поле ввода

### Главное поле (с голосом)
- **Контейнер:** background `--bg-raised`, border 1px `--border`, радиус 12px (`--r-lg`)
- **Высота:** 52px
- **Иконка слева:** 20px, цвет `--text-dim`, padding-left 16px
- **Input:** background transparent, padding 14px 16px 14px 0, font Inter 15px
- **Placeholder:** `--text-dim`

### Состояние focus
- Border: `--accent`
- Box-shadow: `0 0 0 3px var(--accent-soft)` (12% opacity glow)

### Голосовая кнопка
- Размер: 40×40
- Background: `--accent`
- Цвет иконки: `--bg`
- Радиус: 8px
- Отступ от края: 6px
- Иконка: ti-microphone 20px

### Состояние "Слушаю"
- Background: `rgba(248, 81, 73, 0.1)`
- Border: `--red`
- Icon: ti-player-stop-filled, цвет `--red`
- Animation: pulse 1.5s ease-in-out infinite

### Чипсы-подсказки
- Под полем, gap 8px, flex-wrap
- Background: `--bg-raised`, border 1px `--border`
- Padding: 6px 12px
- Радиус: 999px (full pill)
- Font: 12px / 400, цвет `--text-mute`
- Hover: border `--accent`, color `--accent`

---

## 6. Бейджи

### Параметры
- Padding: 4px 10px
- Радиус: 999px (full pill)
- Font: 11px / 600 / letter-spacing 0.03em / UPPERCASE
- Icon: 12px, gap 6px

### Варианты
- **Success** (выгода): bg `rgba(63, 185, 80, 0.15)`, color `--green`
- **Accent** (Лучшая цена, Premium): bg `--accent-soft`, color `--accent`
- **Warning** (Подорожал): bg `rgba(210, 153, 34, 0.15)`, color `--amber`
- **Danger** (Накрутка): bg `rgba(248, 81, 73, 0.15)`, color `--red`
- **Info** (Скидка сезонная): bg `rgba(88, 166, 255, 0.15)`, color `--blue`
- **Mute** (нейтральное): bg `--bg-raised`, color `--text-mute`

### Правила
- Не более 1-2 бейджей на карточку
- Не использовать как кнопки — только индикаторы

---

## 7. Состояния загрузки

### Этапы поиска (главное)
Список из 5 этапов в порядке выполнения. Каждый этап в одном из 3 состояний:

**Pending (ожидает)**
- Background: `--bg-raised`
- Icon: ti-circle 20px, цвет `--text-dim`
- Text: 14px, цвет `--text-dim`

**Active (выполняется сейчас)**
- Background: `--bg-raised`
- Border: 1px `--accent`
- Spinner: 24×24, border 2px `--border`, top-color `--accent`, animation spin 0.8s linear infinite
- Text: 14px, цвет `--text`

**Done (готово)**
- Background: `--accent-soft`
- Icon: ti-check 20px, цвет `--accent`
- Text: 14px, цвет `--text`

### Skeleton (для списков)
- Background: linear-gradient(90deg, `--bg-raised` 0%, `--bg-high` 50%, `--bg-raised` 100%)
- Background-size: 200% 100%
- Animation: shimmer 1.5s ease-in-out infinite (background-position: 200% → -200%)
- Радиус: 6px

---

## 8. Empty states

### Структура
- Padding: 48px 24px
- Flex column, align-items center, text-align center

### Иконка
- Размер: 64×64
- Background: `--bg-raised`
- Радиус: 999px (круг)
- Icon: 28px, цвет `--text-dim`
- Margin-bottom: 16px

### Текст
- Title: 17px / 600, margin-bottom 6px
- Description: 13px / `--text-mute`, max-width 260px, margin-bottom 20px

### CTA
- Primary кнопка под текстом

---

## 9. Пейволл

### Контейнер
- Background: `--bg-surface`
- Border: 1px `--accent`
- Радиус: 16px (`--r-xl`)
- Padding: 24px
- Декоративный radial gradient в правом верхнем углу: `radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)`, 240×240, position top:-100px right:-100px

### Структура
1. Бейдж "Premium" (badge--accent с иконкой ti-bolt)
2. Title 22px / 700
3. Description 14px / `--text-mute`
4. Список фич с галочками: 14px, иконка ti-check 18px `--accent`
5. Карточки тарифов (2 штуки)
6. CTA-кнопка primary large block
7. Caption внизу: "Отмена в любой момент"

### Карточки тарифов
- Border: 1px `--border` (default), `--accent` (selected)
- Background: transparent (default), `--accent-soft` (selected)
- Padding: 14px 16px
- Радиус: 8px
- Layout: flex justify-between
- Left: название тарифа (Body 14 / 500) + sub (Caption 12)
- Right: цена (monospace 16 / 600) + скидка (11px `--accent`)

### Якорь
- Годовая по умолчанию выбрана, показана первой
- Месячная — для тех кто "не уверен"
- CTA: "7 дней бесплатно" (не "Купить")

---

## 10. Bottom sheet

### Контейнер
- Position: fixed bottom
- Background: `--bg-surface`
- Border-top-radius: 16px (`--r-xl`)
- Border-top: 1px `--border`
- Padding: 8px 20px 24px
- Box-shadow: `0 -8px 32px rgba(0,0,0,0.5)`

### Handle (индикатор swipe)
- Размер: 40×4
- Background: `--bg-high`
- Радиус: 999px (full)
- Margin: 0 auto 16px

### Title
- Font: 17px / 600
- Margin-bottom: 16px

### Опции
- Layout: flex column gap 4px
- Каждая опция: padding 12px 16px, радиус 8px, flex align-center gap 12px
- Icon: 20px, цвет `--text-mute`
- Text: 15px
- Hover: background `--bg-raised`

### Правила использования
- Использовать для: выбора опций, шеринга, уточнения запроса
- НЕ использовать для: критичных подтверждений (там нужен модал на весь экран)
- Открытие: slide-up 300ms ease-out
- Закрытие: tap на handle или backdrop

---

## Общие токены

### Радиусы
- `--r-sm`: 6px (skeleton, мелкие элементы)
- `--r-md`: 8px (кнопки, плашки)
- `--r-lg`: 12px (карточки, поля ввода)
- `--r-xl`: 16px (большие контейнеры, paywall, bottom sheet)
- `--r-full`: 999px (pill-формы, бейджи, круги)

### Anim
- `--t-fast`: 150ms (микро-анимации)
- `--t-base`: 200ms (стандарт для кнопок, ховеров)
- `--t-slow`: 400ms (переходы экранов, big reveals)
- `--ease`: `cubic-bezier(0.16, 1, 0.3, 1)` — единственный easing функция в проекте

### Отступы (рекомендация)
- 4px: микро (между иконкой и текстом)
- 8px: малый (между связанными элементами)
- 12px: средний (между элементами внутри блока)
- 16px: базовый (padding контейнеров на мобильном)
- 24px: большой (padding контейнеров на десктопе)
- 32px: секция (между логическими блоками)
- 48px: страница (между секциями)

### Тени
В целом не используем — flat дизайн. Исключения:
- Box-shadow на bottom sheet: `0 -8px 32px rgba(0,0,0,0.5)`
- Box-shadow focus-ring на input: `0 0 0 3px var(--accent-soft)`

---

## Иконки

**Библиотека:** Tabler Icons (outline-стиль)

**Подключение:**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.0.0/dist/tabler-icons.min.css">
```

**Использование:**
```html
<i class="ti ti-search"></i>
<i class="ti ti-microphone"></i>
<i class="ti ti-bell"></i>
```

**Размеры:**
- 16px — inline в тексте
- 18px — в кнопках, маленьких элементах
- 20px — стандарт UI (в полях ввода, опциях меню)
- 24px — заголовки секций, иконки этапов
- 28px — empty state иконки
- 48px — hero иконки

**Часто используемые:**
- ti-search, ti-microphone, ti-bell, ti-share, ti-heart
- ti-check, ti-x, ti-alert-triangle, ti-info-circle
- ti-arrow-right, ti-chevron-down, ti-arrow-up-right
- ti-home, ti-settings, ti-user, ti-history
- ti-shopping-cart, ti-tag, ti-currency-rubel
- ti-brand-telegram, ti-brand-whatsapp

---

## Что НЕ делаем (анти-паттерны)

❌ Не используем градиенты (кроме одного декоративного на пейволле)
❌ Не используем тени (кроме функциональных)
❌ Не используем bouncy/spring анимации (только cubic-bezier выше)
❌ Не используем эмодзи в декоративных целях (только функциональные 🥇🥈🥉 ✅⚠️❌)
❌ Не используем размер шрифта меньше 11px
❌ Не используем размер кнопки меньше 36px высотой
❌ Не используем больше 3 цветов на экране (фон + текст + один акцент)
❌ Не используем confetti, fireworks, sparkles

---

## Файлы

- `index.html` — интерактивная дизайн-система, открыть в браузере
- `spec.md` — этот документ

Версия: 1.0 · Май 2026
