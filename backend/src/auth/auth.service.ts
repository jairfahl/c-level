import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';

interface User {
  id: string;
  username: string;
  role: string;
}

const HARDCODED_USERS: User[] = [
  { id: 'admin', username: 'admin', role: 'CFO' },
];

@Injectable()
export class AuthService {
  constructor(private readonly jwtService: JwtService) {}

  validateUser(username: string, password: string): User | null {
    // In production this would query the users table
    if (username === 'admin' && password === 'admin123') {
      return HARDCODED_USERS[0];
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
