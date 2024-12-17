import argparse
import random
import time

def main():
    # Парсим аргументы гиперпараметров
    parser = argparse.ArgumentParser()
    parser.add_argument("--learning_rate", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--n_steps", type=int, default=100, help="Number of steps")
    args = parser.parse_args()

    # Логирование гиперпараметров
    print(f"Starting training with:")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Batch size: {args.batch_size}")
    print(f"Number of steps: {args.n_steps}")

    # Имитация обучения
    time.sleep(1)

    # Генерация результата обучения
    # Для демонстрации: результат зависит от гиперпараметров, но с некоторым случайным элементом
    score = (
        1000 / args.learning_rate +
        args.batch_size / 10 +
        random.uniform(-10, 10)
    ) / args.n_steps

    # Вывод результата
    print(f"Total Reward: {score}")

if __name__ == "__main__":
    main()
