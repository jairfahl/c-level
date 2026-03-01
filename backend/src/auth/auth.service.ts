import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';

interface User {
  id: string;
  username: string;
  role: string;
}

@Injectable()
export class AuthService {
  constructor(
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  validateUser(username: string, password: string): User | null {
    // In production replace with a proper users table and bcrypt password hashing
    const adminUsername = this.configService.get<string>('ADMIN_USERNAME') || 'admin';
    const adminPassword = this.configService.get<string>('ADMIN_PASSWORD') || 'admin123';
    if (username === adminUsername && password === adminPassword) {
      return { id: adminUsername, username: adminUsername, role: 'CFO' };
    }
    return null;
  }

  login(user: User): { access_token: string; user: User } {
    const payload = { sub: user.id, username: user.username, role: user.role };
    return {
      access_token: this.jwtService.sign(payload),
      user,
    };
  }
}
