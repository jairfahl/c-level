import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { FinancialDecisionCasesModule } from './financial-decision-cases/financial-decision-cases.module';
import { LlmModule } from './llm/llm.module';
import { HealthController } from './health.controller';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    PrismaModule,
    AuthModule,
    FinancialDecisionCasesModule,
    LlmModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
