# 🎨 Design Playbook (shadcn/ui) — Правила дизайна в Nakama

> Руководство по дизайну интерфейсов с использованием **shadcn/ui** и **Tailwind CSS**.
> Версия: 1.0 | Актуально для: 2026

## 🎯 1. Философия дизайна shadcn/ui

### Основные принципы

```
✅ МИНИМАЛИЗМ — чистый, не перегруженный интерфейс
✅ ФУНКЦИОНАЛЬНОСТЬ — дизайн служит функции
✅ ACCESSIBILITY — доступность для всех пользователей
✅ КОНСИСТЕНТНОСТЬ — единая система токенов
✅ ТЕМИЗАЦИЯ — поддержка светлой и тёмной темы
```

### Стиль shadcn/ui

shadcn/ui предлагает два стиля:

| Стиль | Описание | Когда использовать |
|-------|----------|-------------------|
| **Default** | Более мягкий, скругленный | Пользовательские приложения |
| **New York** | Строгий, минималистичный | Админ-панели, дашборды |

Для Nakama рекомендуется **New York** — профессиональный стиль для бизнес-приложений.

---

## 🎨 2. Цветовая система (CSS переменные)

### Семантические цвета

shadcn/ui использует **семантические переменные** вместо конкретных цветов:

```
background / foreground      — Основной фон и текст
card / card-foreground       — Карточки
popover / popover-foreground — Выпадающие меню
primary / primary-foreground — Главный акцент
secondary / secondary-foreground — Вторичный
muted / muted-foreground     — Приглушенный
accent / accent-foreground   — Акцент (hover)
destructive / destructive-foreground — Ошибки, удаление
border                       — Границы
input                        — Поля ввода
ring                         — Focus ring
```

### Цветовая палитра (Neutral)

**Светлая тема:**

| Переменная | Цвет | HEX (примерно) | Использование |
|------------|------|----------------|---------------|
| `--background` | Белый | `#ffffff` | Основной фон |
| `--foreground` | Почти чёрный | `#0a0a0a` | Основной текст |
| `--card` | Белый | `#ffffff` | Фон карточек |
| `--primary` | Тёмно-серый | `#171717` | Кнопки, акценты |
| `--secondary` | Светло-серый | `#f5f5f5` | Вторичные кнопки |
| `--muted` | Очень светлый | `#f5f5f5` | Приглушенный фон |
| `--muted-foreground` | Серый | `#737373` | Вторичный текст |
| `--destructive` | Красный | `#ef4444` | Ошибки, удаление |
| `--border` | Светло-серый | `#e5e5e5` | Границы |

**Тёмная тема:**

| Переменная | Цвет | HEX (примерно) | Использование |
|------------|------|----------------|---------------|
| `--background` | Почти чёрный | `#0a0a0a` | Основной фон |
| `--foreground` | Почти белый | `#fafafa` | Основной текст |
| `--card` | Тёмно-серый | `#171717` | Фон карточек |
| `--primary` | Светло-серый | `#e5e5e5` | Кнопки, акценты |
| `--secondary` | Тёмный | `#262626` | Вторичные кнопки |
| `--muted` | Тёмный | `#262626` | Приглушенный фон |
| `--muted-foreground` | Серый | `#a3a3a3` | Вторичный текст |
| `--destructive` | Светло-красный | `#dc2626` | Ошибки |

### Цветовой формат OKLCH

shadcn/ui использует **OKLCH** — современный цветовой формат:

```css
/* Пример */
--primary: oklch(0.205 0 0);  /* Почти чёрный в светлой теме */
--primary: oklch(0.922 0 0);  /* Почти белый в тёмной теме */
```

**Почему OKLCH:**
- Perceptually uniform (воспринимаемая равномерность)
- Лучшие переходы между цветами
- Проще создавать палитры

### Кастомизация цветов

Для брендирования Nakama можно заменить `neutral` на цветной акцент:

```css
/* Пример: зелёный акцент (ваш --primary: #42b983) */
:root {
  --primary: oklch(0.696 0.17 162.48);  /* Зелёный */
  --primary-foreground: oklch(0.985 0 0); /* Белый текст */
}
```

---

## 📝 3. Типографика

### Шрифт

**Основной шрифт:** `Wix Madefor Display` (сохраняем из текущего дизайна)

**Fallback:** `Inter, -apple-system, BlinkMacSystemFont, sans-serif`

### Tailwind классы для текста

| Назначение | Tailwind класс | Размер |
|------------|----------------|--------|
| H1 (заголовок страницы) | `text-2xl font-semibold` | 24px |
| H2 (заголовок секции) | `text-xl font-semibold` | 20px |
| H3 (подзаголовок) | `text-lg font-medium` | 18px |
| H4 (заголовок карточки) | `text-base font-medium` | 16px |
| Body (основной) | `text-sm` | 14px |
| Small (вторичный) | `text-xs` | 12px |
| Muted (приглушенный) | `text-sm text-muted-foreground` | 14px |

### Примеры

```tsx
<h1 className="text-2xl font-semibold tracking-tight">
  Заголовок страницы
</h1>

<p className="text-sm text-muted-foreground">
  Вторичный текст или описание
</p>

<span className="text-xs font-medium">
  Мета-информация
</span>
```

### Цвета текста

| Назначение | Tailwind класс |
|------------|----------------|
| Основной текст | `text-foreground` |
| Вторичный текст | `text-muted-foreground` |
| На primary кнопке | `text-primary-foreground` |
| Ошибка | `text-destructive` |
| Ссылка | `text-primary hover:underline` |

---

## 📐 4. Spacing (отступы)

### Система отступов Tailwind

Tailwind использует шкалу кратную 4px:

| Класс | Значение | Использование |
|-------|----------|---------------|
| `p-1`, `m-1` | 4px | Минимальный |
| `p-2`, `m-2` | 8px | Между связанными элементами |
| `p-3`, `m-3` | 12px | Внутри компонентов |
| `p-4`, `m-4` | 16px | Стандартный padding карточек |
| `p-6`, `m-6` | 24px | Между секциями |
| `p-8`, `m-8` | 32px | Между крупными блоками |

### Gap для flexbox/grid

```tsx
// Между элементами
<div className="flex gap-2">...</div>   // 8px
<div className="flex gap-4">...</div>   // 16px
<div className="grid gap-6">...</div>   // 24px
```

### Space для вертикальных списков

```tsx
// Автоматические отступы между детьми
<div className="space-y-2">...</div>   // 8px между элементами
<div className="space-y-4">...</div>   // 16px между элементами
```

---

## 🔲 5. Компоненты shadcn/ui

### Button (Кнопки)

**Варианты:**

| Variant | Внешний вид | Использование |
|---------|-------------|---------------|
| `default` | Тёмный фон, светлый текст | Главное действие |
| `secondary` | Светлый фон, тёмный текст | Вторичное действие |
| `outline` | Прозрачный с рамкой | Отмена, третичное |
| `ghost` | Без фона, только текст | Навигация, иконки |
| `link` | Как ссылка | Текстовые ссылки |
| `destructive` | Красный | Удаление, опасные действия |

**Размеры:**

| Size | Padding | Использование |
|------|---------|---------------|
| `default` | `h-9 px-4 py-2` | Стандартный |
| `sm` | `h-8 px-3` | Компактный |
| `lg` | `h-10 px-8` | Крупный CTA |
| `icon` | `h-9 w-9` | Иконка-кнопка |

**Примеры:**

```tsx
<Button>Default</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>
<Button size="sm">Small</Button>
<Button size="icon"><Plus className="h-4 w-4" /></Button>
```

### Input (Поля ввода)

**Структура:**

```
┌─────────────────────────────────────┐
│ Label                               │
│ ┌─────────────────────────────────┐ │
│ │ Placeholder text                │ │
│ └─────────────────────────────────┘ │
│ Helper text / Error message         │
└─────────────────────────────────────┘
```

**Состояния:**

| Состояние | Классы |
|-----------|--------|
| Default | `border-input bg-background` |
| Focus | `ring-2 ring-ring ring-offset-2` |
| Error | `border-destructive` |
| Disabled | `disabled:opacity-50 disabled:cursor-not-allowed` |

**Пример:**

```tsx
<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input 
    id="email" 
    type="email" 
    placeholder="name@example.com" 
  />
  <p className="text-sm text-muted-foreground">
    Мы никогда не поделимся вашим email
  </p>
</div>
```

### Card (Карточки)

**Структура:**

```tsx
<Card>
  <CardHeader>
    <CardTitle>Заголовок</CardTitle>
    <CardDescription>Описание карточки</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Основной контент */}
  </CardContent>
  <CardFooter>
    {/* Кнопки действий */}
  </CardFooter>
</Card>
```

**Стили:**

```
bg-card              — Фон карточки
text-card-foreground — Цвет текста
rounded-lg           — Скругление (var(--radius))
border               — Рамка
shadow-sm            — Тень (опционально)
```

### Dialog (Модальные окна)

```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button>Открыть</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Заголовок</DialogTitle>
      <DialogDescription>
        Описание модального окна
      </DialogDescription>
    </DialogHeader>
    {/* Контент */}
    <DialogFooter>
      <Button variant="outline">Отмена</Button>
      <Button>Подтвердить</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Размеры Dialog:**

| Класс | Ширина |
|-------|--------|
| `sm:max-w-sm` | 384px |
| `sm:max-w-md` | 448px (default) |
| `sm:max-w-lg` | 512px |
| `sm:max-w-xl` | 576px |

### Table (Таблицы)

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Название</TableHead>
      <TableHead>Статус</TableHead>
      <TableHead className="text-right">Действия</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell className="font-medium">Проект 1</TableCell>
      <TableCell>
        <Badge variant="secondary">Активен</Badge>
      </TableCell>
      <TableCell className="text-right">
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </TableCell>
    </TableRow>
  </TableBody>
</Table>
```

---

## 🎭 6. Иконки (Lucide)

### Библиотека

shadcn/ui использует **Lucide React** — форк Feather Icons с большим набором иконок.

```bash
npm install lucide-react
```

### Использование

```tsx
import { Search, Plus, Trash2, Settings, ChevronRight } from "lucide-react"

<Search className="h-4 w-4" />
<Plus className="h-4 w-4" />
```

### Размеры

| Контекст | Классы | Пример |
|----------|--------|--------|
| В кнопке SM | `h-3 w-3` | Маленькие кнопки |
| В кнопке | `h-4 w-4` | Стандартные кнопки |
| В навигации | `h-5 w-5` | Sidebar |
| Standalone | `h-6 w-6` | Заголовки |

### Иконка с текстом

```tsx
<Button>
  <Plus className="mr-2 h-4 w-4" />
  Добавить
</Button>

// Иконка справа
<Button>
  Далее
  <ChevronRight className="ml-2 h-4 w-4" />
</Button>
```

---

## 🔄 7. Анимации

### Встроенные анимации Tailwind

```tsx
// Спиннер загрузки
<Loader2 className="h-4 w-4 animate-spin" />

// Пульсация
<div className="animate-pulse bg-muted h-4 w-full rounded" />

// Bounce
<div className="animate-bounce" />
```

### Transitions

```tsx
// Плавный переход цвета
<button className="transition-colors hover:bg-accent" />

// Все свойства
<div className="transition-all duration-200" />

// Кастомная длительность
<div className="transition-opacity duration-300" />
```

### Анимация появления (для модалок)

```css
@keyframes in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes out {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.95); }
}
```

---

## 🌙 8. Тёмная тема

### Автоматическое переключение

shadcn/ui использует класс `.dark` на `<html>`:

```tsx
// Светлая тема
<html>...</html>

// Тёмная тема
<html class="dark">...</html>
```

### Адаптивные цвета

Все компоненты автоматически меняют цвета:

```tsx
// Этот код работает в обеих темах!
<div className="bg-background text-foreground">
  <Card>
    <CardContent className="text-muted-foreground">
      Контент
    </CardContent>
  </Card>
</div>
```

### Кастомные стили для тем

```tsx
// Разные стили для светлой и тёмной
<div className="bg-white dark:bg-slate-900" />

// Разные цвета текста
<p className="text-gray-900 dark:text-gray-100" />
```

---

## 📐 9. Layouts

### Sidebar Layout

```tsx
<div className="flex min-h-screen">
  {/* Sidebar */}
  <aside className="sticky top-0 h-screen w-[106px] border-r bg-sidebar">
    <nav className="flex flex-col gap-4 p-4">
      {/* Navigation items */}
    </nav>
  </aside>
  
  {/* Main content */}
  <main className="flex-1 p-6">
    {children}
  </main>
</div>
```

### Page Container

```tsx
<div className="container mx-auto max-w-7xl px-4 py-6">
  {/* Page content */}
</div>
```

### Centered Card (Login page)

```tsx
<div className="flex min-h-screen items-center justify-center bg-muted p-4">
  <Card className="w-full max-w-md">
    {/* Form content */}
  </Card>
</div>
```

### List Page

```tsx
<div className="space-y-6">
  {/* Header */}
  <div className="flex items-center justify-between">
    <h1 className="text-2xl font-semibold">Проекты</h1>
    <Button>
      <Plus className="mr-2 h-4 w-4" />
      Создать
    </Button>
  </div>
  
  {/* Filters */}
  <div className="flex gap-4">
    <Input placeholder="Поиск..." className="max-w-sm" />
    <Button variant="outline">Фильтры</Button>
  </div>
  
  {/* Table */}
  <Card>
    <Table>...</Table>
  </Card>
  
  {/* Pagination */}
  <div className="flex justify-end gap-2">
    <Button variant="outline" size="sm">Назад</Button>
    <Button variant="outline" size="sm">Вперёд</Button>
  </div>
</div>
```

---

## 📝 10. Состояния интерфейса

### Empty State

```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <div className="rounded-full bg-muted p-4">
    <Inbox className="h-8 w-8 text-muted-foreground" />
  </div>
  <h3 className="mt-4 text-lg font-medium">Нет проектов</h3>
  <p className="mt-2 text-sm text-muted-foreground">
    Создайте первый проект, чтобы начать работу
  </p>
  <Button className="mt-4">
    <Plus className="mr-2 h-4 w-4" />
    Создать проект
  </Button>
</div>
```

### Loading State

```tsx
// Spinner
<div className="flex items-center justify-center py-12">
  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
</div>

// Skeleton
<div className="space-y-4">
  <Skeleton className="h-4 w-[250px]" />
  <Skeleton className="h-4 w-[200px]" />
  <Skeleton className="h-4 w-[300px]" />
</div>
```

### Error State

```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <div className="rounded-full bg-destructive/10 p-4">
    <AlertTriangle className="h-8 w-8 text-destructive" />
  </div>
  <h3 className="mt-4 text-lg font-medium">Что-то пошло не так</h3>
  <p className="mt-2 text-sm text-muted-foreground">
    Не удалось загрузить данные. Попробуйте обновить страницу.
  </p>
  <Button variant="outline" className="mt-4">
    Обновить страницу
  </Button>
</div>
```

### Toast / Notification

```tsx
import { toast } from "sonner"

// Success
toast.success("Проект успешно создан")

// Error
toast.error("Не удалось сохранить изменения")

// With description
toast("Проект сохранён", {
  description: "Все изменения успешно применены",
})
```

---

## ♿ 11. Accessibility

### Встроенная поддержка

shadcn/ui построен на **Radix UI**, который обеспечивает:

```
✅ Правильные ARIA атрибуты
✅ Клавиатурная навигация
✅ Focus management
✅ Screen reader support
✅ Правильная семантика HTML
```

### Focus Ring

```css
/* Автоматически применяется к интерактивным элементам */
focus-visible:outline-none 
focus-visible:ring-2 
focus-visible:ring-ring 
focus-visible:ring-offset-2
```

### Screen Reader Only

```tsx
// Текст только для screen readers
<span className="sr-only">Открыть меню</span>
```

### Контраст

| Комбинация | Соответствие WCAG |
|------------|-------------------|
| `foreground` на `background` | ✅ AAA |
| `muted-foreground` на `background` | ✅ AA |
| `primary-foreground` на `primary` | ✅ AA |

---

## 🔧 12. Работа с разработкой

### Figma → Tailwind

При передаче макетов указывайте Tailwind классы:

```
Фон: bg-card
Текст: text-foreground / text-muted-foreground
Отступы: p-4, gap-4
Размер: w-full max-w-md
Скругление: rounded-lg (var(--radius))
```

### Naming Convention

| В Figma | В коде |
|---------|--------|
| Button / Default | `<Button>` |
| Button / Destructive | `<Button variant="destructive">` |
| Input / Default | `<Input>` |
| Card / Default | `<Card>` |

### Передача дизайна

1. **Figma Dev Mode** — включить для разработчиков
2. **Указывать классы** — добавлять Tailwind классы в описание
3. **Цвета через переменные** — использовать `--primary`, не конкретные HEX
4. **Состояния** — показывать все состояния компонентов

---

## ✅ 13. Чеклист дизайна

### Компоненты
- [ ] Используются стандартные компоненты shadcn/ui
- [ ] Все состояния отрисованы (default, hover, focus, disabled, error)
- [ ] Варианты соответствуют (default, secondary, outline, destructive...)

### Цвета
- [ ] Используются семантические переменные (не конкретные HEX)
- [ ] Работает в светлой И тёмной теме
- [ ] Контраст текста минимум 4.5:1

### Отступы
- [ ] Используется система кратная 4px (p-2, p-4, p-6...)
- [ ] Консистентные gap между элементами

### Адаптивность
- [ ] Desktop версия
- [ ] Планшет (md breakpoint)
- [ ] Мобильная версия (sm breakpoint)

### Состояния страниц
- [ ] Empty state
- [ ] Loading state (skeleton или spinner)
- [ ] Error state

---

## ⚡ 14. Quick Reference

### Цветовые переменные

| Переменная | Светлая | Тёмная |
|------------|---------|--------|
| `--background` | Белый | Чёрный |
| `--foreground` | Чёрный | Белый |
| `--card` | Белый | Тёмно-серый |
| `--primary` | Чёрный | Светлый |
| `--secondary` | Светло-серый | Тёмно-серый |
| `--muted` | Светло-серый | Тёмно-серый |
| `--muted-foreground` | Серый | Серый |
| `--destructive` | Красный | Красный |
| `--border` | Светло-серый | Прозрачный белый |

### Tailwind классы

| Категория | Классы |
|-----------|--------|
| Фон | `bg-background`, `bg-card`, `bg-muted`, `bg-primary` |
| Текст | `text-foreground`, `text-muted-foreground`, `text-primary` |
| Границы | `border`, `border-input`, `border-destructive` |
| Скругления | `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-full` |
| Тени | `shadow-sm`, `shadow-md`, `shadow-lg` |
| Spacing | `p-2`, `p-4`, `p-6`, `gap-2`, `gap-4`, `space-y-4` |

### Компоненты

| Компонент | Варианты |
|-----------|----------|
| Button | `default`, `secondary`, `outline`, `ghost`, `link`, `destructive` |
| Badge | `default`, `secondary`, `outline`, `destructive` |
| Alert | `default`, `destructive` |

### Размеры

| Компонент | Размеры |
|-----------|---------|
| Button | `default`, `sm`, `lg`, `icon` |
| Input | Стандартный (h-9) |
| Avatar | `sm`, `default`, `lg` |

---

*Этот playbook — живой документ. Обновляйте его по мере развития дизайн-системы.*

