import { Module } from '@nestjs/common';
import { FinancialDecisionCasesController } from './financial-decision-cases.controller';
import { FinancialDecisionCasesService } from './financial-decision-cases.service';
import { StateMachineService } from './state-machine.service';
import { PrismaModule } from '../prisma/prisma.module';
import { LlmModule } from '../llm/llm.module';

@Module({
  imports: [PrismaModule, LlmModule],
  controllers: [FinancialDecisionCasesController],
  providers: [FinancialDecisionCasesService, StateMachineService],
  exports: [FinancialDecisionCasesService],
})
export class FinancialDecisionCasesModule {}
