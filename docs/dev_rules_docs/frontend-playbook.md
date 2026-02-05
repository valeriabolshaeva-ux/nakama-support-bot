# 📘 Frontend Playbook (shadcn/ui) — Правила фронтенд-разработки в Nakama

> Руководство для разработки фронтенд-приложений с использованием **shadcn/ui** и **Tailwind CSS**.
> Версия: 1.0 | Актуально для: 2026

## 📁 1. Структура проекта (Feature-Sliced Design + shadcn)

```
src/
├── app/                    # 🎛️ Инициализация приложения
│   ├── layout/
│   ├── providers/
│   ├── router/
│   ├── store/
│   └── styles/
│       ├── globals.css     # Tailwind + CSS переменные темы
│       └── tailwind.css    # @tailwind директивы
│
├── components/             # 🧱 shadcn/ui компоненты (NEW!)
│   └── ui/                 # Базовые UI компоненты
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── table.tsx
│       ├── form.tsx
│       └── ...
│
├── entities/               # 📦 Бизнес-сущности
│   └── [entity]/
│       ├── api/
│       ├── model/
│       ├── slice/
│       └── ui/             # Компоненты БЕЗ .module.css!
│
├── features/               # 🔧 Пользовательские сценарии
│   └── [feature]/
│       ├── index.ts
│       ├── model/
│       ├── ui/
│       │   └── Feature.tsx  # Tailwind классы вместо CSS Modules
│       └── utils/
│
├── lib/                    # 📚 Утилиты (NEW!)
│   └── utils.ts            # cn() функция для классов
│
├── pages/
├── shared/
└── widgets/
```

### Новые папки для shadcn/ui

| Папка | Назначение |
|-------|------------|
| `src/components/ui/` | shadcn/ui компоненты (Button, Input, Dialog...) |
| `src/lib/` | Утилиты (`cn`, хелперы) |

---

## 🛠️ 2. Установка и настройка

### Зависимости

```bash
# Основные зависимости для shadcn/ui
npm install tailwindcss @tailwindcss/vite
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react  # Иконки
npm install tw-animate-css # Анимации

# Для форм (опционально)
npm install react-hook-form @hookform/resolvers zod

# Для таблиц (опционально)  
npm install @tanstack/react-table
```

### Инициализация shadcn/ui

```bash
npx shadcn init
```

При инициализации выбрать:
- Style: `new-york` или `default`
- Base color: `neutral` / `slate` / `zinc`
- CSS variables: `yes`

### Конфигурация Vite

```typescript
// vite.config.ts
import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
```

### Конфигурация components.json

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/styles/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/shared/hooks"
  },
  "iconLibrary": "lucide"
}
```

---

## 🎨 3. Стилизация с Tailwind CSS

### Золотые правила

```
✅ Используем Tailwind utility классы напрямую в JSX
✅ cn() функция для условных/динамических классов
✅ CSS переменные для темы (цвета, радиусы)
✅ Один globals.css для переменных темы
❌ НЕ используем CSS Modules (.module.css)
❌ НЕ используем inline styles (style={})
❌ НЕ используем @apply в CSS (только в крайних случаях)
```

### Утилита cn() для классов

```typescript
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Использование:**

```tsx
import { cn } from "@/lib/utils"

// Простое объединение
<div className={cn("flex items-center", className)} />

// Условные классы
<button className={cn(
  "px-4 py-2 rounded-md",
  isActive && "bg-primary text-primary-foreground",
  isDisabled && "opacity-50 cursor-not-allowed"
)} />

// Переопределение классов (twMerge разрешит конфликты)
<div className={cn("p-4", "p-8")} />  // Результат: "p-8"
```

### Глобальные стили и CSS переменные

```css
/* src/app/styles/globals.css */
@import "tailwindcss";

/* ===== ТЕМА: СВЕТЛАЯ ===== */
:root {
  --radius: 0.625rem;
  
  /* Фоны */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  
  /* Карточки */
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  
  /* Popover/Dropdown */
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  
  /* Primary (основной акцент) */
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  
  /* Secondary */
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  
  /* Muted (приглушенный) */
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  
  /* Accent */
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  
  /* Destructive (ошибки, удаление) */
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.985 0 0);
  
  /* Границы и инпуты */
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
  
  /* Sidebar */
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.145 0 0);
  --sidebar-primary: oklch(0.205 0 0);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.97 0 0);
  --sidebar-accent-foreground: oklch(0.205 0 0);
  --sidebar-border: oklch(0.922 0 0);
}

/* ===== ТЕМА: ТЁМНАЯ ===== */
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  
  --popover: oklch(0.269 0 0);
  --popover-foreground: oklch(0.985 0 0);
  
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  
  --accent: oklch(0.371 0 0);
  --accent-foreground: oklch(0.985 0 0);
  
  --destructive: oklch(0.704 0.191 22.216);
  --destructive-foreground: oklch(0.985 0 0);
  
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
  
  --sidebar: oklch(0.205 0 0);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.269 0 0);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(1 0 0 / 10%);
}

/* ===== БАЗОВЫЕ СТИЛИ ===== */
body {
  font-family: 'Wix Madefor Display', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

---

## 📝 4. Компоненты shadcn/ui

### Добавление компонентов

```bash
# Добавить отдельный компонент
npx shadcn add button
npx shadcn add input
npx shadcn add card
npx shadcn add dialog
npx shadcn add table
npx shadcn add form

# Добавить несколько сразу
npx shadcn add button input card dialog
```

### Структура компонента shadcn/ui

```tsx
// src/components/ui/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Базовые классы (всегда применяются)
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

### Использование компонентов

```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

function LoginForm() {
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Войти в систему</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input 
          type="email" 
          placeholder="Email" 
          className="w-full"
        />
        <Input 
          type="password" 
          placeholder="Пароль" 
        />
        <Button className="w-full">
          Войти
        </Button>
        <Button variant="outline" className="w-full">
          Отмена
        </Button>
      </CardContent>
    </Card>
  )
}
```

---

## 🔄 5. Миграция компонентов: до и после

### Кнопка

**Было (Chakra UI + CSS Modules):**
```tsx
// Button.tsx
import styles from './Button.module.css'

export function Button({ children, variant = 'primary', size = 'medium' }) {
  return (
    <button className={`${styles.button} ${styles[`button${variant}`]} ${styles[`button${size}`]}`}>
      {children}
    </button>
  )
}
```

**Стало (shadcn/ui):**
```tsx
import { Button } from "@/components/ui/button"

// Использование
<Button variant="default" size="default">Click me</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline" size="sm">Cancel</Button>
```

### Форма входа

**Было (Chakra UI):**
```tsx
import { HStack, Spinner } from '@chakra-ui/react';
import styles from './LoginForm.module.css';

export function LoginForm() {
  return (
    <div className={styles.loginPage}>
      <div className={styles.loginCard}>
        <input className={styles.inputField} />
        <button className={styles.loginButton}>
          {isLoading ? <Spinner /> : 'Войти'}
        </button>
      </div>
    </div>
  );
}
```

**Стало (shadcn/ui + Tailwind):**
```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

export function LoginForm() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <CardTitle>Добро пожаловать</CardTitle>
          <p className="text-sm text-muted-foreground">
            Введите ваши учетные данные
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input type="email" placeholder="Email" />
          <Input type="password" placeholder="Пароль" />
          <Button className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

### Sidebar

**Было (Chakra UI):**
```tsx
import { Flex, VStack } from '@chakra-ui/react';

export const Sidebar = () => {
  return (
    <Flex
      as="aside"
      direction="column"
      position="sticky"
      top="0"
      height="100vh"
      width="106px"
      bg="layout.sidebar"
      justifyContent="space-between"
    >
      <VStack gap="7">
        <SidebarNavigation />
      </VStack>
    </Flex>
  );
};
```

**Стало (shadcn/ui + Tailwind):**
```tsx
export const Sidebar = () => {
  return (
    <aside className="sticky top-0 flex h-screen w-[106px] flex-col justify-between bg-sidebar p-4">
      <nav className="flex flex-col gap-7">
        <SidebarNavigation />
      </nav>
      <SidebarLogout />
    </aside>
  )
}
```

---

## 📋 6. Формы с react-hook-form и zod

### Установка

```bash
npm install react-hook-form @hookform/resolvers zod
npx shadcn add form input label
```

### Пример формы

```tsx
"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

// Схема валидации
const loginSchema = z.object({
  email: z.string().email("Введите корректный email"),
  password: z.string().min(8, "Пароль минимум 8 символов"),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginForm() {
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  function onSubmit(values: LoginFormValues) {
    console.log(values)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input placeholder="example@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Пароль</FormLabel>
              <FormControl>
                <Input type="password" placeholder="••••••••" {...field} />
              </FormControl>
              <FormDescription>
                Минимум 8 символов
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button type="submit" className="w-full">
          Войти
        </Button>
      </form>
    </Form>
  )
}
```

---

## 📊 7. Таблицы с TanStack Table

### Установка

```bash
npm install @tanstack/react-table
npx shadcn add table
```

### DataTable компонент

```tsx
"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchKey?: string
  searchPlaceholder?: string
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
  searchPlaceholder = "Поиск...",
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
  })

  return (
    <div className="space-y-4">
      {/* Поиск */}
      {searchKey && (
        <Input
          placeholder={searchPlaceholder}
          value={(table.getColumn(searchKey)?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn(searchKey)?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
      )}

      {/* Таблица */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  Нет данных
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Пагинация */}
      <div className="flex items-center justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Назад
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Вперёд
        </Button>
      </div>
    </div>
  )
}
```

---

## 🎭 8. Иконки (Lucide React)

### Использование

```tsx
import { 
  Search, 
  Plus, 
  Trash2, 
  Settings, 
  User,
  ChevronRight,
  Loader2,
  Check,
  X
} from "lucide-react"

// В компонентах
<Button>
  <Plus className="mr-2 h-4 w-4" />
  Добавить
</Button>

// Иконка-кнопка
<Button variant="ghost" size="icon">
  <Settings className="h-4 w-4" />
</Button>

// Спиннер загрузки
<Loader2 className="h-4 w-4 animate-spin" />
```

### Размеры иконок

| Размер | Классы | Использование |
|--------|--------|---------------|
| XS | `h-3 w-3` | Badges, мелкие индикаторы |
| SM | `h-4 w-4` | В кнопках, инпутах |
| MD | `h-5 w-5` | Навигация |
| LG | `h-6 w-6` | Заголовки секций |
| XL | `h-8 w-8` | Hero секции |

---

## 🌙 9. Тёмная тема

### Провайдер темы

```tsx
// src/app/providers/ThemeProvider.tsx
import { createContext, useContext, useEffect, useState } from "react"

type Theme = "dark" | "light" | "system"

interface ThemeProviderProps {
  children: React.ReactNode
  defaultTheme?: Theme
}

const ThemeContext = createContext<{
  theme: Theme
  setTheme: (theme: Theme) => void
}>({
  theme: "system",
  setTheme: () => null,
})

export function ThemeProvider({ 
  children, 
  defaultTheme = "system" 
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(defaultTheme)

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove("light", "dark")

    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches ? "dark" : "light"
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
```

### Переключатель темы

```tsx
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/app/providers/ThemeProvider"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
```

---

## 🧪 10. Тестирование

### Тестирование компонентов shadcn/ui

```tsx
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Button } from "@/components/ui/button"

describe("Button", () => {
  it("renders correctly", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole("button")).toHaveTextContent("Click me")
  })

  it("handles click", async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    await userEvent.click(screen.getByRole("button"))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Click me</Button>)
    expect(screen.getByRole("button")).toBeDisabled()
  })
})
```

---

## ✅ 11. Чеклист миграции

### Удалить
- [ ] Удалить `@chakra-ui/react` и `@emotion/*` из зависимостей
- [ ] Удалить файлы `.module.css`
- [ ] Удалить `chakra-system.ts` и `ChakraProvider.tsx`

### Установить
- [ ] Установить `tailwindcss`, `@tailwindcss/vite`
- [ ] Установить `class-variance-authority`, `clsx`, `tailwind-merge`
- [ ] Установить `lucide-react`
- [ ] Запустить `npx shadcn init`
- [ ] Добавить нужные компоненты через `npx shadcn add`

### Настроить
- [ ] Создать `src/lib/utils.ts` с функцией `cn()`
- [ ] Настроить `globals.css` с CSS переменными
- [ ] Обновить `vite.config.ts`
- [ ] Создать `components.json`

### Мигрировать
- [ ] Заменить Chakra компоненты на shadcn/ui
- [ ] Заменить CSS Modules классы на Tailwind
- [ ] Обновить формы на react-hook-form + zod

---

## ⚡ 12. Quick Reference

### Tailwind классы (частые)

| Назначение | Классы |
|------------|--------|
| Flex container | `flex items-center justify-between gap-4` |
| Grid | `grid grid-cols-3 gap-4` |
| Spacing | `p-4 px-6 py-2 m-4 mx-auto` |
| Sizing | `w-full h-screen min-h-[400px] max-w-md` |
| Typography | `text-sm font-medium text-muted-foreground` |
| Border | `border rounded-md border-input` |
| Background | `bg-background bg-card bg-muted` |
| Shadow | `shadow-sm shadow-md shadow-lg` |
| Transitions | `transition-colors duration-200` |

### Компоненты shadcn/ui

```bash
npx shadcn add button input card dialog table form
npx shadcn add dropdown-menu select checkbox radio-group
npx shadcn add toast alert badge avatar
npx shadcn add tabs accordion collapsible
npx shadcn add calendar date-picker
```

### Файлы проекта

| Файл | Назначение |
|------|------------|
| `components.json` | Конфигурация shadcn/ui |
| `src/lib/utils.ts` | Утилита cn() |
| `src/app/styles/globals.css` | CSS переменные темы |
| `src/components/ui/` | shadcn/ui компоненты |

---

*Этот playbook — живой документ. Обновляйте его по мере миграции.*

