<?php

namespace App\Console;

use App\Model\Facade\Cron;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Exception\LogicException;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Attribute\AsCommand;

#[AsCommand(name: 'app:embeddings')]
final class EmbeddingsCommand extends Command
{
    protected Cron $cron;

    /**
     * @param string|null $name The name of the command; passing null means it must be set in configure()
     *
     * @throws LogicException When the command name is empty
     */
    public function __construct(Cron $cron)
    {
        parent::__construct();
        $this->cron = $cron;
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        try {
            $this->cron->makeEmbeddingsCommand();
            $output->writeln('Embedding - done');
        } catch (\Exception $ex) {
            $output->writeln('Embedding - FAILED');
            $output->writeln($ex->getMessage());
        }
        return self::SUCCESS;
    }

}